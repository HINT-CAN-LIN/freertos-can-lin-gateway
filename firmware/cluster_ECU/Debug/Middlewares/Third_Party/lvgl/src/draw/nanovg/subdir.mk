################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_3d.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_arc.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_blur.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_border.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_box_shadow.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_fill.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_grad.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_image.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_label.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_layer.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_line.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_mask_rect.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_triangle.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_vector.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_fbo_cache.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_image_cache.c \
../Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_utils.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_3d.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_arc.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_blur.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_border.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_box_shadow.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_fill.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_grad.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_image.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_label.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_layer.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_line.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_mask_rect.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_triangle.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_vector.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_fbo_cache.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_image_cache.o \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_utils.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_3d.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_arc.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_blur.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_border.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_box_shadow.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_fill.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_grad.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_image.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_label.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_layer.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_line.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_mask_rect.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_triangle.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_vector.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_fbo_cache.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_image_cache.d \
./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_utils.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/draw/nanovg/%.o Middlewares/Third_Party/lvgl/src/draw/nanovg/%.su Middlewares/Third_Party/lvgl/src/draw/nanovg/%.cyclo: ../Middlewares/Third_Party/lvgl/src/draw/nanovg/%.c Middlewares/Third_Party/lvgl/src/draw/nanovg/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-nanovg

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-nanovg:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_3d.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_3d.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_3d.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_3d.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_arc.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_arc.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_arc.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_arc.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_blur.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_blur.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_blur.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_blur.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_border.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_border.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_border.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_border.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_box_shadow.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_box_shadow.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_box_shadow.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_box_shadow.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_fill.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_fill.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_fill.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_fill.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_grad.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_grad.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_grad.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_grad.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_image.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_image.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_image.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_image.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_label.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_label.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_label.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_label.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_layer.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_layer.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_layer.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_layer.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_line.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_line.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_line.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_line.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_mask_rect.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_mask_rect.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_mask_rect.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_mask_rect.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_triangle.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_triangle.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_triangle.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_triangle.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_vector.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_vector.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_vector.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_draw_nanovg_vector.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_fbo_cache.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_fbo_cache.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_fbo_cache.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_fbo_cache.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_image_cache.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_image_cache.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_image_cache.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_image_cache.su ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_utils.cyclo ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_utils.d ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_utils.o ./Middlewares/Third_Party/lvgl/src/draw/nanovg/lv_nanovg_utils.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-nanovg

