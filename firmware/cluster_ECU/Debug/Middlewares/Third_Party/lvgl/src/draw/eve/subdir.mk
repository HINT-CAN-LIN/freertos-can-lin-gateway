################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve.c \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_arc.c \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_fill.c \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_image.c \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_letter.c \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_line.c \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_ram_g.c \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_triangle.c \
../Middlewares/Third_Party/lvgl/src/draw/eve/lv_eve.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve.o \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_arc.o \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_fill.o \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_image.o \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_letter.o \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_line.o \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_ram_g.o \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_triangle.o \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_eve.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve.d \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_arc.d \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_fill.d \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_image.d \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_letter.d \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_line.d \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_ram_g.d \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_triangle.d \
./Middlewares/Third_Party/lvgl/src/draw/eve/lv_eve.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/draw/eve/%.o Middlewares/Third_Party/lvgl/src/draw/eve/%.su Middlewares/Third_Party/lvgl/src/draw/eve/%.cyclo: ../Middlewares/Third_Party/lvgl/src/draw/eve/%.c Middlewares/Third_Party/lvgl/src/draw/eve/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-eve

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-eve:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve.su ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_arc.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_arc.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_arc.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_arc.su ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_fill.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_fill.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_fill.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_fill.su ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_image.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_image.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_image.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_image.su ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_letter.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_letter.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_letter.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_letter.su ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_line.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_line.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_line.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_line.su ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_ram_g.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_ram_g.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_ram_g.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_ram_g.su ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_triangle.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_triangle.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_triangle.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_draw_eve_triangle.su ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_eve.cyclo ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_eve.d ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_eve.o ./Middlewares/Third_Party/lvgl/src/draw/eve/lv_eve.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-eve

