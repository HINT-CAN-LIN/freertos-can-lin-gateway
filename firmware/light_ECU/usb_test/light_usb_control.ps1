# Run with Windows PowerShell: powershell -NoProfile -STA -ExecutionPolicy Bypass -File .\light_usb_control.ps1
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$script:port=$null
$script:rx=''
$script:connectedAt=[DateTime]::MinValue
$script:lastRx=[DateTime]::MinValue
$form=New-Object Windows.Forms.Form
$form.Text='Light ECU - USB bench (115200 baud)'
$form.ClientSize=New-Object Drawing.Size(700,340)
$form.StartPosition='CenterScreen'
$ports=New-Object Windows.Forms.ComboBox
$ports.SetBounds(20,20,140,30)
$ports.DropDownStyle='DropDownList'
$form.Controls.Add($ports)
$refresh=New-Object Windows.Forms.Button
$refresh.Text='Refresh ports';$refresh.SetBounds(170,20,120,30);$form.Controls.Add($refresh)
$connect=New-Object Windows.Forms.Button
$connect.Text='Connect';$connect.SetBounds(300,20,120,30);$form.Controls.Add($connect)
$send=New-Object Windows.Forms.CheckBox
$send.Text='Send every 50 ms';$send.SetBounds(440,20,230,30);$send.Enabled=$false;$form.Controls.Add($send)
$script:checks=@{}
$labels=@('Head','Left','Right','Hazard','Reverse','Brake')
for($i=0;$i -lt $labels.Count;$i++) {
  $c=New-Object Windows.Forms.CheckBox
  $c.Text=$labels[$i];$c.SetBounds(20+($i%3)*220,80+[int][Math]::Floor($i/3)*45,200,30)
  $script:checks[$labels[$i]]=$c;$form.Controls.Add($c)
}
$checks.Left.Add_CheckedChanged({if($checks.Left.Checked){$checks.Right.Checked=$false}})
$checks.Right.Add_CheckedChanged({if($checks.Right.Checked){$checks.Left.Checked=$false}})
$off=New-Object Windows.Forms.Button
$off.Text='ALL OFF';$off.SetBounds(20,175,150,40);$form.Controls.Add($off)
$status=New-Object Windows.Forms.Label
$status.SetBounds(20,230,660,55);$status.Text='Connect ST-LINK USB, then select its COM port.';$form.Controls.Add($status)
$hint=New-Object Windows.Forms.Label
$hint.SetBounds(20,290,660,40);$hint.Text='Uncheck Send to test the 250 ms timeout. No CAN/LIN hardware is needed.';$form.Controls.Add($hint)
function Refresh-Ports {
  $ports.Items.Clear()
  [IO.Ports.SerialPort]::GetPortNames() | Sort-Object | ForEach-Object {[void]$ports.Items.Add($_)}
  if($ports.Items.Count -gt 0){$ports.SelectedIndex=0}
}
function Disconnect-Port {
  $send.Checked=$false;$send.Enabled=$false
  if($script:port){
    try {if($script:port.IsOpen){$script:port.Write("S00`n");$script:port.Close()}} catch {}
    $script:port.Dispose();$script:port=$null
  }
  $connect.Text='Connect';$ports.Enabled=$true;$refresh.Enabled=$true
}
$refresh.Add_Click({Refresh-Ports})
$connect.Add_Click({
  if($script:port){Disconnect-Port;$status.Text='Disconnected; outputs time out within 250 ms.';return}
  if(!$ports.SelectedItem){$status.Text='No COM port selected.';return}
  try {
    $script:port=New-Object IO.Ports.SerialPort([string]$ports.SelectedItem,115200,[IO.Ports.Parity]::None,8,[IO.Ports.StopBits]::One)
    $script:port.Handshake=[IO.Ports.Handshake]::None
    $script:port.WriteTimeout=100;$script:port.ReadTimeout=50
    $script:port.Open();$script:port.DiscardInBuffer();$script:rx=''
    foreach($c in $checks.Values){$c.Checked=$false}
    $script:connectedAt=[DateTime]::UtcNow;$script:lastRx=[DateTime]::MinValue
    $send.Enabled=$true;$send.Checked=$true;$ports.Enabled=$false;$refresh.Enabled=$false
    $connect.Text='Disconnect';$status.Text='Waiting for LIGHT1 firmware status...'
  } catch {Disconnect-Port;$status.Text='Open failed: '+$_.Exception.Message}
})
$off.Add_Click({
  foreach($c in $checks.Values){$c.Checked=$false}
  if($script:port -and $script:port.IsOpen){try{$script:port.Write("S00`n")}catch{Disconnect-Port}}
})
$timer=New-Object Windows.Forms.Timer
$timer.Interval=50
$timer.Add_Tick({
  if(!$script:port){return}
  try {
    $script:rx+=$script:port.ReadExisting()
    while(($idx=$script:rx.IndexOf("`n")) -ge 0){
      $line=$script:rx.Substring(0,$idx).Trim();$script:rx=$script:rx.Substring($idx+1)
      if($line -match '^LIGHT1 cmd=[0-9A-F]{2} lamps=[0-9A-F]{2} out=[0-9A-F]{2} diag=[0-2] alive=\d+ err=\d+$'){
        $status.Text=$line;$script:lastRx=[DateTime]::UtcNow
      }
    }
    if($script:rx.Length -gt 4096){$script:rx=''}
    $reference=$script:lastRx
    if($reference -eq [DateTime]::MinValue){$reference=$script:connectedAt}
    if(([DateTime]::UtcNow-$reference).TotalMilliseconds -gt 1000){
      $send.Checked=$false
      $status.Text='No fresh LIGHT1 response. Sending stopped; check firmware/COM port. Reconnect to retry.'
      return
    }
    if($send.Checked){
      $value=0
      if($checks.Head.Checked){$value=$value -bor 1}
      if($checks.Left.Checked){$value=$value -bor 2}
      if($checks.Right.Checked){$value=$value -bor 4}
      if($checks.Hazard.Checked){$value=$value -bor 8}
      if($checks.Reverse.Checked){$value=$value -bor 16}
      if($checks.Brake.Checked){$value=$value -bor 32}
      $script:port.Write(('S{0:X2}' -f $value)+"`n")
    }
  } catch {Disconnect-Port;$status.Text='Serial error: '+$_.Exception.Message}
})
$form.Add_FormClosing({$timer.Stop();Disconnect-Port})
Refresh-Ports
$timer.Start()
[void]$form.ShowDialog()
$timer.Dispose();$form.Dispose()
