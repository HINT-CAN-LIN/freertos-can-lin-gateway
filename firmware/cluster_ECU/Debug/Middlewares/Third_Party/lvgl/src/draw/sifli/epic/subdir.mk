################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_buf_sifli_epic.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_border.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_fill.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_img.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_label.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_layer.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_cfg.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_osa.c \
../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_utils.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_buf_sifli_epic.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_border.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_fill.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_img.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_label.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_layer.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_cfg.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_osa.o \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_utils.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_buf_sifli_epic.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_border.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_fill.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_img.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_label.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_layer.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_cfg.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_osa.d \
./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_utils.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/draw/sifli/epic/%.o Middlewares/Third_Party/lvgl/src/draw/sifli/epic/%.su Middlewares/Third_Party/lvgl/src/draw/sifli/epic/%.cyclo: ../Middlewares/Third_Party/lvgl/src/draw/sifli/epic/%.c Middlewares/Third_Party/lvgl/src/draw/sifli/epic/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-sifli-2f-epic

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-sifli-2f-epic:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_buf_sifli_epic.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_buf_sifli_epic.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_buf_sifli_epic.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_buf_sifli_epic.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_border.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_border.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_border.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_border.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_fill.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_fill.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_fill.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_fill.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_img.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_img.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_img.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_img.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_label.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_label.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_label.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_label.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_layer.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_layer.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_layer.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_draw_sifli_epic_layer.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_cfg.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_cfg.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_cfg.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_cfg.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_osa.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_osa.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_osa.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_osa.su ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_utils.cyclo ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_utils.d ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_utils.o ./Middlewares/Third_Party/lvgl/src/draw/sifli/epic/lv_sifli_epic_utils.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-draw-2f-sifli-2f-epic

