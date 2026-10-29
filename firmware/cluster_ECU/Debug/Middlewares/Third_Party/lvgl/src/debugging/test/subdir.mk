################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display.c \
../Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display_egl.c \
../Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_fs.c \
../Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_helpers.c \
../Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev.c \
../Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev_gesture.c \
../Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_screenshot_compare.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display.o \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display_egl.o \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_fs.o \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_helpers.o \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev.o \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev_gesture.o \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_screenshot_compare.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display.d \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display_egl.d \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_fs.d \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_helpers.d \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev.d \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev_gesture.d \
./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_screenshot_compare.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/debugging/test/%.o Middlewares/Third_Party/lvgl/src/debugging/test/%.su Middlewares/Third_Party/lvgl/src/debugging/test/%.cyclo: ../Middlewares/Third_Party/lvgl/src/debugging/test/%.c Middlewares/Third_Party/lvgl/src/debugging/test/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-debugging-2f-test

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-debugging-2f-test:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display.cyclo ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display.d ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display.o ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display.su ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display_egl.cyclo ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display_egl.d ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display_egl.o ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_display_egl.su ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_fs.cyclo ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_fs.d ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_fs.o ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_fs.su ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_helpers.cyclo ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_helpers.d ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_helpers.o ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_helpers.su ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev.cyclo ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev.d ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev.o ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev.su ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev_gesture.cyclo ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev_gesture.d ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev_gesture.o ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_indev_gesture.su ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_screenshot_compare.cyclo ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_screenshot_compare.d ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_screenshot_compare.o ./Middlewares/Third_Party/lvgl/src/debugging/test/lv_test_screenshot_compare.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-debugging-2f-test

