################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/widgets/gif/lv_gif.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/widgets/gif/lv_gif.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/widgets/gif/lv_gif.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/widgets/gif/%.o Middlewares/Third_Party/lvgl/src/widgets/gif/%.su Middlewares/Third_Party/lvgl/src/widgets/gif/%.cyclo: ../Middlewares/Third_Party/lvgl/src/widgets/gif/%.c Middlewares/Third_Party/lvgl/src/widgets/gif/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-widgets-2f-gif

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-widgets-2f-gif:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/widgets/gif/lv_gif.cyclo ./Middlewares/Third_Party/lvgl/src/widgets/gif/lv_gif.d ./Middlewares/Third_Party/lvgl/src/widgets/gif/lv_gif.o ./Middlewares/Third_Party/lvgl/src/widgets/gif/lv_gif.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-widgets-2f-gif

