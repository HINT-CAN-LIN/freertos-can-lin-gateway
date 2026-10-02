################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/drivers/draw/eve/lv_draw_eve_display.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/drivers/draw/eve/lv_draw_eve_display.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/drivers/draw/eve/lv_draw_eve_display.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/drivers/draw/eve/%.o Middlewares/Third_Party/lvgl/src/drivers/draw/eve/%.su Middlewares/Third_Party/lvgl/src/drivers/draw/eve/%.cyclo: ../Middlewares/Third_Party/lvgl/src/drivers/draw/eve/%.c Middlewares/Third_Party/lvgl/src/drivers/draw/eve/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-draw-2f-eve

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-draw-2f-eve:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/drivers/draw/eve/lv_draw_eve_display.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/draw/eve/lv_draw_eve_display.d ./Middlewares/Third_Party/lvgl/src/drivers/draw/eve/lv_draw_eve_display.o ./Middlewares/Third_Party/lvgl/src/drivers/draw/eve/lv_draw_eve_display.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-draw-2f-eve

