"""고정 TEST ONLY Catalog/Assertion 계약. Hardware/Production Fault 시험 아님."""
from dataclasses import replace
import pytest
from pc_diagnostic import DbcLoader
from pc_diagnostic.interfaces import CanInterfaceError
from pc_diagnostic.gui.automation import (AssertionSpec, MAX_ASSERTIONS, MAX_SCENARIO_FRAMES,
                                         ScenarioInput, catalog, evaluate, fixture_path,
                                         validate_catalog, validate_fixture)


def test_catalog_has_unique_stable_bounded_contracts():
    # 동일 ID가 같은 입력/기대값 계약을 의미하며 요구 feature kind를 포함한다.
    first, second = catalog(),catalog()
    assert first==second and len({item.scenario_id for item in first})==len(first)
    assert {item.kind for item in first}=={"raw","decode","decode-error","cache","vehicle","ecu","fault","graph","jsonl","csv","source"}
    assert all(0<len(item.input_frames)<=MAX_SCENARIO_FRAMES and 0<len(item.assertions)<=MAX_ASSERTIONS for item in first)
    assert all("TEST ONLY" in item.input_source for item in first)


def test_catalog_can_ids_format_signals_exist_in_unchanged_fixture():
    # 실제 DBC metadata를 읽으며 새로운 ID/Signal/bit layout을 생성하지 않는다.
    path=validate_fixture(fixture_path())
    loader=DbcLoader().load(path)
    for scenario in catalog():
        for frame in scenario.input_frames:
            definition=loader.get_message_by_id(frame.arbitration_id,is_extended_id=frame.is_extended_id)
            assert definition.is_extended_frame is frame.is_extended_id
    sample=loader.get_message_by_name("TestOnlySample")
    assert {s.name for s in sample.signals}=={"Measurement","Mode","Counter"}
    assert next(s for s in sample.signals if s.name=="Measurement").unit=="test_unit"


@pytest.mark.parametrize("invalid", ["duplicate-id","unknown-kind","frames","assertions","duplicate-assertion"])
def test_invalid_catalog_is_rejected_before_execution(invalid):
    # 중복 및 무한/미지원 계약은 Catalog 시작 전에 거부한다.
    scenario=catalog()[0]
    if invalid=="duplicate-id":
        values=(scenario,replace(scenario,name="another"))
    elif invalid=="unknown-kind":
        values=(replace(scenario,kind="external-python-script"),)
    elif invalid=="frames":
        values=(replace(scenario,input_frames=(scenario.input_frames[0],)*(MAX_SCENARIO_FRAMES+1)),)
    elif invalid=="assertions":
        values=(replace(scenario,assertions=tuple(AssertionSpec(str(i),1) for i in range(MAX_ASSERTIONS+1))),)
    else:
        values=(replace(scenario,assertions=(AssertionSpec("x",1),AssertionSpec("x",1))),)
    with pytest.raises(ValueError):
        validate_catalog(values)


def test_fixture_version_change_is_not_silently_accepted(tmp_path):
    # Golden fixture 변경 시 동일 ID의 기대값을 새 Decode 결과로 다시 만들지 않는다.
    changed=tmp_path/"changed.dbc"
    changed.write_bytes(fixture_path().read_bytes()+b"\n")
    with pytest.raises(ValueError,match="Unsupported DBC"):
        validate_fixture(changed)


@pytest.mark.parametrize("actual,expected", [({},1),({"value":2},1),({},None)])
def test_missing_or_wrong_actual_never_passes(actual,expected):
    # 성공 주입이나 기대값만 있는 상태를 PASS로 취급하지 않는다.
    result=evaluate((AssertionSpec("value",expected),),actual)[0]
    assert result.passed is False and result.reason
    assert result.expected==expected and result.actual==actual.get("value","NOT OBSERVED")


def test_assertion_success_uses_separate_expected_and_actual():
    # 실제값을 사후 수정해도 불변 AssertionResult의 기대값은 그대로이다.
    actual={"value":3}
    result=evaluate((AssertionSpec("value",3),),actual)[0]
    actual["value"]=4
    assert result.passed and result.actual==3 and result.expected==3


def test_scenario_input_is_gated_fifo_and_rx_only():
    # 실제 Bus 객체 없이 기존 Mock FIFO를 조합하고 send 오용을 검출한다.
    frames=catalog()[0].input_frames
    stream=ScenarioInput(frames)
    assert stream.recv(0) is None
    stream.release.set()
    assert stream.recv(0) is frames[0] and stream.recv(0) is frames[1]
    assert stream.recv(0) is None
    with pytest.raises(CanInterfaceError,match="prohibited"):
        stream.send(frames[0])
    assert stream.send_calls==1 and stream.mock.sent_frames==()
    stream.shutdown();stream.shutdown()
    assert stream.shutdown_calls==1 and stream.closed.is_set()
    assert stream.recv(0) is None
