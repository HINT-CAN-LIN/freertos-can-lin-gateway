/**
 * @file lv_test.h
 *
 */

#ifndef LV_TEST_H
#define LV_TEST_H

#ifdef __cplusplus
extern "C" {
#endif

/*********************
 *      INCLUDES
 *********************/
#include <lvgl/config/lv_conf_internal.h>
#if LV_USE_TEST

/*********************
 *      DEFINES
 *********************/
#include <lvgl/debugging/test/lv_test_indev.h>
#include <lvgl/debugging/test/lv_test_display.h>
#include <lvgl/debugging/test/lv_test_fs.h>
#include <lvgl/debugging/test/lv_test_helpers.h>
#include <lvgl/debugging/test/lv_test_screenshot_compare.h>
#include <lvgl/debugging/test/lv_test_indev_gesture.h>

/**********************
 *      TYPEDEFS
 **********************/

/**********************
 * GLOBAL PROTOTYPES
 **********************/

/**********************
 *      MACROS
 **********************/

#endif /*LV_USE TEST*/

#ifdef __cplusplus
} /*extern "C"*/
#endif

#endif /*LV_TEST_H*/
