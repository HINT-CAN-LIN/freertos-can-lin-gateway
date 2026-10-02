################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa.c \
../Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_buf.c \
../Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_fill.c \
../Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_img.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa.o \
./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_buf.o \
./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_fill.o \
./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_img.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa.d \
./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_buf.d \
./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_fill.d \
./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_img.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/%.o Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/%.su Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/%.cyclo: ../Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/%.c Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-espressif-2f-ppa

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-espressif-2f-ppa:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa.cyclo ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa.d ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa.o ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa.su ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_buf.cyclo ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_buf.d ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_buf.o ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_buf.su ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_fill.cyclo ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_fill.d ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_fill.o ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_fill.su ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_img.cyclo ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_img.d ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_img.o ./Middlewares/Third_Party/lvgl/src/draw/espressif/ppa/lv_draw_ppa_img.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-espressif-2f-ppa

