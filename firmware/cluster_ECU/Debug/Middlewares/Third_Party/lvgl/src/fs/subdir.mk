################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs.c \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs_fatfs.c \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs_frogfs.c \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs_littlefs.c \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs_memfs.c \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs_posix.c \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs_stdio.c \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs_uefi.c \
../Middlewares/Third_Party/lvgl/src/fs/lv_fs_win32.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs.o \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_fatfs.o \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_frogfs.o \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_littlefs.o \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_memfs.o \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_posix.o \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_stdio.o \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_uefi.o \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_win32.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs.d \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_fatfs.d \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_frogfs.d \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_littlefs.d \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_memfs.d \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_posix.d \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_stdio.d \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_uefi.d \
./Middlewares/Third_Party/lvgl/src/fs/lv_fs_win32.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/fs/%.o Middlewares/Third_Party/lvgl/src/fs/%.su Middlewares/Third_Party/lvgl/src/fs/%.cyclo: ../Middlewares/Third_Party/lvgl/src/fs/%.c Middlewares/Third_Party/lvgl/src/fs/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-fs

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-fs:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/fs/lv_fs.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs.su ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_fatfs.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_fatfs.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_fatfs.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_fatfs.su ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_frogfs.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_frogfs.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_frogfs.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_frogfs.su ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_littlefs.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_littlefs.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_littlefs.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_littlefs.su ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_memfs.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_memfs.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_memfs.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_memfs.su ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_posix.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_posix.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_posix.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_posix.su ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_stdio.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_stdio.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_stdio.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_stdio.su ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_uefi.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_uefi.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_uefi.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_uefi.su ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_win32.cyclo ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_win32.d ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_win32.o ./Middlewares/Third_Party/lvgl/src/fs/lv_fs_win32.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-fs

