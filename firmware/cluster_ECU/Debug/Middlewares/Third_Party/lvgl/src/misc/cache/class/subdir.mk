################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_ll.c \
../Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_rb.c \
../Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_sc_da.c 

OBJS += \
./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_ll.o \
./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_rb.o \
./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_sc_da.o 

C_DEPS += \
./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_ll.d \
./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_rb.d \
./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_sc_da.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/Third_Party/lvgl/src/misc/cache/class/%.o Middlewares/Third_Party/lvgl/src/misc/cache/class/%.su Middlewares/Third_Party/lvgl/src/misc/cache/class/%.cyclo: ../Middlewares/Third_Party/lvgl/src/misc/cache/class/%.c Middlewares/Third_Party/lvgl/src/misc/cache/class/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_NUCLEO_64 -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Middlewares/Third_Party/lvgl/include -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/BSP/STM32F4xx-Nucleo -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-misc-2f-cache-2f-class

clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-misc-2f-cache-2f-class:
	-$(RM) ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_ll.cyclo ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_ll.d ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_ll.o ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_ll.su ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_rb.cyclo ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_rb.d ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_rb.o ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_lru_rb.su ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_sc_da.cyclo ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_sc_da.d ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_sc_da.o ./Middlewares/Third_Party/lvgl/src/misc/cache/class/lv_cache_sc_da.su

.PHONY: clean-Middlewares-2f-Third_Party-2f-lvgl-2f-src-2f-misc-2f-cache-2f-class

