################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/egl.c \
../Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gl.c \
../Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gles2.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/egl.o \
./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gl.o \
./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gles2.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/egl.d \
./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gl.d \
./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gles2.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/%.o Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/%.su Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/%.cyclo: ../Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/%.c Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-opengles-2f-glad-2f-src

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-opengles-2f-glad-2f-src:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/egl.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/egl.d ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/egl.o ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/egl.su ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gl.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gl.d ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gl.o ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gl.su ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gles2.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gles2.d ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gles2.o ./Middlewares/Third_Party/lvgl/src/drivers/opengles/glad/src/gles2.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-opengles-2f-glad-2f-src

