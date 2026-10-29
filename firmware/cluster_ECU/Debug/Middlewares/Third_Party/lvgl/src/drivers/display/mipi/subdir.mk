################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_ili9341.c \
../Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_lcd_generic_mipi.c \
../Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_nv3007.c \
../Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7735.c \
../Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7789.c \
../Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7796.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_ili9341.o \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_lcd_generic_mipi.o \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_nv3007.o \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7735.o \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7789.o \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7796.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_ili9341.d \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_lcd_generic_mipi.d \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_nv3007.d \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7735.d \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7789.d \
./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7796.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/drivers/display/mipi/%.o Middlewares/Third_Party/lvgl/src/drivers/display/mipi/%.su Middlewares/Third_Party/lvgl/src/drivers/display/mipi/%.cyclo: ../Middlewares/Third_Party/lvgl/src/drivers/display/mipi/%.c Middlewares/Third_Party/lvgl/src/drivers/display/mipi/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-display-2f-mipi

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-display-2f-mipi:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_ili9341.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_ili9341.d ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_ili9341.o ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_ili9341.su ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_lcd_generic_mipi.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_lcd_generic_mipi.d ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_lcd_generic_mipi.o ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_lcd_generic_mipi.su ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_nv3007.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_nv3007.d ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_nv3007.o ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_nv3007.su ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7735.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7735.d ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7735.o ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7735.su ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7789.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7789.d ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7789.o ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7789.su ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7796.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7796.d ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7796.o ./Middlewares/Third_Party/lvgl/src/drivers/display/mipi/lv_st7796.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-display-2f-mipi

