################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/image/lv_bin_decoder.c \
../Middlewares/Third_Party/lvgl/src/image/lv_bmp.c \
../Middlewares/Third_Party/lvgl/src/image/lv_image_decoder.c \
../Middlewares/Third_Party/lvgl/src/image/lv_libjpeg_turbo.c \
../Middlewares/Third_Party/lvgl/src/image/lv_libpng.c \
../Middlewares/Third_Party/lvgl/src/image/lv_libwebp.c \
../Middlewares/Third_Party/lvgl/src/image/lv_lodepng.c \
../Middlewares/Third_Party/lvgl/src/image/lv_tjpgd.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/image/lv_bin_decoder.o \
./Middlewares/Third_Party/lvgl/src/image/lv_bmp.o \
./Middlewares/Third_Party/lvgl/src/image/lv_image_decoder.o \
./Middlewares/Third_Party/lvgl/src/image/lv_libjpeg_turbo.o \
./Middlewares/Third_Party/lvgl/src/image/lv_libpng.o \
./Middlewares/Third_Party/lvgl/src/image/lv_libwebp.o \
./Middlewares/Third_Party/lvgl/src/image/lv_lodepng.o \
./Middlewares/Third_Party/lvgl/src/image/lv_tjpgd.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/image/lv_bin_decoder.d \
./Middlewares/Third_Party/lvgl/src/image/lv_bmp.d \
./Middlewares/Third_Party/lvgl/src/image/lv_image_decoder.d \
./Middlewares/Third_Party/lvgl/src/image/lv_libjpeg_turbo.d \
./Middlewares/Third_Party/lvgl/src/image/lv_libpng.d \
./Middlewares/Third_Party/lvgl/src/image/lv_libwebp.d \
./Middlewares/Third_Party/lvgl/src/image/lv_lodepng.d \
./Middlewares/Third_Party/lvgl/src/image/lv_tjpgd.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/image/%.o Middlewares/Third_Party/lvgl/src/image/%.su Middlewares/Third_Party/lvgl/src/image/%.cyclo: ../Middlewares/Third_Party/lvgl/src/image/%.c Middlewares/Third_Party/lvgl/src/image/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-image

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-image:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/image/lv_bin_decoder.cyclo ./Middlewares/Third_Party/lvgl/src/image/lv_bin_decoder.d ./Middlewares/Third_Party/lvgl/src/image/lv_bin_decoder.o ./Middlewares/Third_Party/lvgl/src/image/lv_bin_decoder.su ./Middlewares/Third_Party/lvgl/src/image/lv_bmp.cyclo ./Middlewares/Third_Party/lvgl/src/image/lv_bmp.d ./Middlewares/Third_Party/lvgl/src/image/lv_bmp.o ./Middlewares/Third_Party/lvgl/src/image/lv_bmp.su ./Middlewares/Third_Party/lvgl/src/image/lv_image_decoder.cyclo ./Middlewares/Third_Party/lvgl/src/image/lv_image_decoder.d ./Middlewares/Third_Party/lvgl/src/image/lv_image_decoder.o ./Middlewares/Third_Party/lvgl/src/image/lv_image_decoder.su ./Middlewares/Third_Party/lvgl/src/image/lv_libjpeg_turbo.cyclo ./Middlewares/Third_Party/lvgl/src/image/lv_libjpeg_turbo.d ./Middlewares/Third_Party/lvgl/src/image/lv_libjpeg_turbo.o ./Middlewares/Third_Party/lvgl/src/image/lv_libjpeg_turbo.su ./Middlewares/Third_Party/lvgl/src/image/lv_libpng.cyclo ./Middlewares/Third_Party/lvgl/src/image/lv_libpng.d ./Middlewares/Third_Party/lvgl/src/image/lv_libpng.o ./Middlewares/Third_Party/lvgl/src/image/lv_libpng.su ./Middlewares/Third_Party/lvgl/src/image/lv_libwebp.cyclo ./Middlewares/Third_Party/lvgl/src/image/lv_libwebp.d ./Middlewares/Third_Party/lvgl/src/image/lv_libwebp.o ./Middlewares/Third_Party/lvgl/src/image/lv_libwebp.su ./Middlewares/Third_Party/lvgl/src/image/lv_lodepng.cyclo ./Middlewares/Third_Party/lvgl/src/image/lv_lodepng.d ./Middlewares/Third_Party/lvgl/src/image/lv_lodepng.o ./Middlewares/Third_Party/lvgl/src/image/lv_lodepng.su ./Middlewares/Third_Party/lvgl/src/image/lv_tjpgd.cyclo ./Middlewares/Third_Party/lvgl/src/image/lv_tjpgd.d ./Middlewares/Third_Party/lvgl/src/image/lv_tjpgd.o ./Middlewares/Third_Party/lvgl/src/image/lv_tjpgd.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-image

