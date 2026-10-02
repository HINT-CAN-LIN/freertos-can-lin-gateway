################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_dmabuf.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_egl.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_g2d.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_shm.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_dmabuf.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_keyboard.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_pointer.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_seat.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_touch.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_window.c \
../Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_xdg_shell.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_dmabuf.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_egl.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_g2d.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_shm.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_dmabuf.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_keyboard.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_pointer.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_seat.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_touch.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_window.o \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_xdg_shell.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_dmabuf.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_egl.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_g2d.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_shm.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_dmabuf.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_keyboard.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_pointer.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_seat.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_touch.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_window.d \
./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_xdg_shell.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/drivers/wayland/%.o Middlewares/Third_Party/lvgl/src/drivers/wayland/%.su Middlewares/Third_Party/lvgl/src/drivers/wayland/%.cyclo: ../Middlewares/Third_Party/lvgl/src/drivers/wayland/%.c Middlewares/Third_Party/lvgl/src/drivers/wayland/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-wayland

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-wayland:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_dmabuf.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_dmabuf.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_dmabuf.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_dmabuf.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_egl.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_egl.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_egl.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_egl.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_g2d.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_g2d.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_g2d.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_g2d.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_shm.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_shm.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_shm.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_backend_shm.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_dmabuf.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_dmabuf.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_dmabuf.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_dmabuf.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_keyboard.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_keyboard.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_keyboard.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_keyboard.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_pointer.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_pointer.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_pointer.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_pointer.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_seat.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_seat.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_seat.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_seat.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_touch.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_touch.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_touch.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_touch.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_window.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_window.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_window.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_window.su ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_xdg_shell.cyclo ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_xdg_shell.d ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_xdg_shell.o ./Middlewares/Third_Party/lvgl/src/drivers/wayland/lv_wayland_xdg_shell.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-drivers-2f-wayland

