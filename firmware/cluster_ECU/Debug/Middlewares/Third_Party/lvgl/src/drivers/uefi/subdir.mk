################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_context.c \
../Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_display.c \
../Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_keyboard.c \
../Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_pointer.c \
../Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_touch.c \
../Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_private.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_context.o \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_display.o \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_keyboard.o \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_pointer.o \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_touch.o \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_private.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_context.d \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_display.d \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_keyboard.d \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_pointer.d \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_touch.d \
./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_private.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/drivers/uefi/%.o Middlewares/Third_Party/lvgl/src/drivers/uefi/%.su Middlewares/Third_Party/lvgl/src/drivers/uefi/%.cyclo: ../Middlewares/Third_Party/lvgl/src/drivers/uefi/%.c Middlewares/Third_Party/lvgl/src/drivers/uefi/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-uefi

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-uefi:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_context.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_context.d ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_context.o ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_context.su ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_display.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_display.d ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_display.o ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_display.su ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_keyboard.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_keyboard.d ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_keyboard.o ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_keyboard.su ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_pointer.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_pointer.d ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_pointer.o ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_pointer.su ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_touch.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_touch.d ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_touch.o ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_indev_touch.su ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_private.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_private.d ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_private.o ./Middlewares/Third_Party/lvgl/src/drivers/uefi/lv_uefi_private.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-uefi

