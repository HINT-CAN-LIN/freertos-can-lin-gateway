################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/image/svg/lv_svg.c \
../Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_decoder.c \
../Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_parser.c \
../Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_render.c \
../Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_token.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg.o \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_decoder.o \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_parser.o \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_render.o \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_token.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg.d \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_decoder.d \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_parser.d \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_render.d \
./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_token.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/image/svg/%.o Middlewares/Third_Party/lvgl/src/image/svg/%.su Middlewares/Third_Party/lvgl/src/image/svg/%.cyclo: ../Middlewares/Third_Party/lvgl/src/image/svg/%.c Middlewares/Third_Party/lvgl/src/image/svg/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-image-2f-svg

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-image-2f-svg:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg.cyclo ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg.d ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg.o ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg.su ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_decoder.cyclo ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_decoder.d ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_decoder.o ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_decoder.su ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_parser.cyclo ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_parser.d ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_parser.o ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_parser.su ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_render.cyclo ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_render.d ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_render.o ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_render.su ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_token.cyclo ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_token.d ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_token.o ./Middlewares/Third_Party/lvgl/src/image/svg/lv_svg_token.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-image-2f-svg

