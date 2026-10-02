################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype.c \
../Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_glyph.c \
../Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_image.c \
../Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_outline.c \
../Middlewares/Third_Party/lvgl/src/font/freetype/lv_ftsystem.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype.o \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_glyph.o \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_image.o \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_outline.o \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_ftsystem.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype.d \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_glyph.d \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_image.d \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_outline.d \
./Middlewares/Third_Party/lvgl/src/font/freetype/lv_ftsystem.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/font/freetype/%.o Middlewares/Third_Party/lvgl/src/font/freetype/%.su Middlewares/Third_Party/lvgl/src/font/freetype/%.cyclo: ../Middlewares/Third_Party/lvgl/src/font/freetype/%.c Middlewares/Third_Party/lvgl/src/font/freetype/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-font-2f-freetype

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-font-2f-freetype:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype.cyclo ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype.d ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype.o ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype.su ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_glyph.cyclo ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_glyph.d ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_glyph.o ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_glyph.su ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_image.cyclo ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_image.d ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_image.o ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_image.su ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_outline.cyclo ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_outline.d ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_outline.o ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_freetype_outline.su ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_ftsystem.cyclo ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_ftsystem.d ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_ftsystem.o ./Middlewares/Third_Party/lvgl/src/font/freetype/lv_ftsystem.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-font-2f-freetype

