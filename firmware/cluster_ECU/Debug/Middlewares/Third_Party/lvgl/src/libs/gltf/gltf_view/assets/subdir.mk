################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/chromatic.c \
../Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/lv_gltf_view_shader.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/chromatic.o \
./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/lv_gltf_view_shader.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/chromatic.d \
./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/lv_gltf_view_shader.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/%.o Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/%.su Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/%.cyclo: ../Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/%.c Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-libs-2f-gltf-2f-gltf_view-2f-assets

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-libs-2f-gltf-2f-gltf_view-2f-assets:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/chromatic.cyclo ./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/chromatic.d ./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/chromatic.o ./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/chromatic.su ./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/lv_gltf_view_shader.cyclo ./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/lv_gltf_view_shader.d ./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/lv_gltf_view_shader.o ./Middlewares/Third_Party/lvgl/src/libs/gltf/gltf_view/assets/lv_gltf_view_shader.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-libs-2f-gltf-2f-gltf_view-2f-assets

