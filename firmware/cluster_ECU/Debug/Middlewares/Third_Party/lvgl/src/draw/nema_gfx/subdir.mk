################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_arc.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_border.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_cache.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_fill.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_img.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_label.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_layer.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_line.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_stm32_hal.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_triangle.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_utils.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_vector.c \
../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_nema_gfx_path.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_arc.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_border.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_cache.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_fill.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_img.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_label.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_layer.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_line.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_stm32_hal.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_triangle.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_utils.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_vector.o \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_nema_gfx_path.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_arc.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_border.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_cache.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_fill.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_img.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_label.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_layer.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_line.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_stm32_hal.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_triangle.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_utils.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_vector.d \
./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_nema_gfx_path.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/draw/nema_gfx/%.o Middlewares/Third_Party/lvgl/src/draw/nema_gfx/%.su Middlewares/Third_Party/lvgl/src/draw/nema_gfx/%.cyclo: ../Middlewares/Third_Party/lvgl/src/draw/nema_gfx/%.c Middlewares/Third_Party/lvgl/src/draw/nema_gfx/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-nema_gfx

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-nema_gfx:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_arc.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_arc.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_arc.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_arc.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_border.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_border.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_border.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_border.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_cache.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_cache.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_cache.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_cache.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_fill.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_fill.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_fill.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_fill.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_img.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_img.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_img.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_img.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_label.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_label.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_label.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_label.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_layer.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_layer.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_layer.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_layer.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_line.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_line.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_line.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_line.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_stm32_hal.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_stm32_hal.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_stm32_hal.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_stm32_hal.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_triangle.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_triangle.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_triangle.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_triangle.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_utils.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_utils.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_utils.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_utils.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_vector.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_vector.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_vector.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_draw_nema_gfx_vector.su ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_nema_gfx_path.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_nema_gfx_path.d ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_nema_gfx_path.o ./Middlewares/Third_Party/lvgl/src/draw/nema_gfx/lv_nema_gfx_path.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-nema_gfx

