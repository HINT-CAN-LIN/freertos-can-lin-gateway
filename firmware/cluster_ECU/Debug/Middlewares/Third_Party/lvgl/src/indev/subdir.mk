################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/indev/lv_gridnav.c \
../Middlewares/Third_Party/lvgl/src/indev/lv_indev.c \
../Middlewares/Third_Party/lvgl/src/indev/lv_indev_gesture.c \
../Middlewares/Third_Party/lvgl/src/indev/lv_indev_scroll.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/indev/lv_gridnav.o \
./Middlewares/Third_Party/lvgl/src/indev/lv_indev.o \
./Middlewares/Third_Party/lvgl/src/indev/lv_indev_gesture.o \
./Middlewares/Third_Party/lvgl/src/indev/lv_indev_scroll.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/indev/lv_gridnav.d \
./Middlewares/Third_Party/lvgl/src/indev/lv_indev.d \
./Middlewares/Third_Party/lvgl/src/indev/lv_indev_gesture.d \
./Middlewares/Third_Party/lvgl/src/indev/lv_indev_scroll.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/indev/%.o Middlewares/Third_Party/lvgl/src/indev/%.su Middlewares/Third_Party/lvgl/src/indev/%.cyclo: ../Middlewares/Third_Party/lvgl/src/indev/%.c Middlewares/Third_Party/lvgl/src/indev/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-indev

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-indev:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/indev/lv_gridnav.cyclo ./Middlewares/Third_Party/lvgl/src/indev/lv_gridnav.d ./Middlewares/Third_Party/lvgl/src/indev/lv_gridnav.o ./Middlewares/Third_Party/lvgl/src/indev/lv_gridnav.su ./Middlewares/Third_Party/lvgl/src/indev/lv_indev.cyclo ./Middlewares/Third_Party/lvgl/src/indev/lv_indev.d ./Middlewares/Third_Party/lvgl/src/indev/lv_indev.o ./Middlewares/Third_Party/lvgl/src/indev/lv_indev.su ./Middlewares/Third_Party/lvgl/src/indev/lv_indev_gesture.cyclo ./Middlewares/Third_Party/lvgl/src/indev/lv_indev_gesture.d ./Middlewares/Third_Party/lvgl/src/indev/lv_indev_gesture.o ./Middlewares/Third_Party/lvgl/src/indev/lv_indev_gesture.su ./Middlewares/Third_Party/lvgl/src/indev/lv_indev_scroll.cyclo ./Middlewares/Third_Party/lvgl/src/indev/lv_indev_scroll.d ./Middlewares/Third_Party/lvgl/src/indev/lv_indev_scroll.o ./Middlewares/Third_Party/lvgl/src/indev/lv_indev_scroll.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-indev

