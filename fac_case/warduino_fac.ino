
/*
UART Interrupt Example
*/
#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_intr_alloc.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include <stdio.h>
#include <string.h>

/**
 * WARDUINO & WEB ASSEMBLY RELATED DECLARATIONS
 */
#include "WARDuino.h"

WARDuino wac;

unsigned char hello_world_wasm[] = {
  0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00, 0x01, 0x0e, 0x03, 0x60,
  0x01, 0x7f, 0x00, 0x60, 0x00, 0x00, 0x60, 0x02, 0x7e, 0x7f, 0x01, 0x7f,
  0x03, 0x04, 0x03, 0x00, 0x02, 0x01, 0x07, 0x08, 0x01, 0x04, 0x6d, 0x61,
  0x69, 0x6e, 0x00, 0x02, 0x0a, 0x37, 0x03, 0x02, 0x00, 0x0b, 0x1c, 0x00,
  0x20, 0x01, 0x41, 0x01, 0x4a, 0x04, 0x7f, 0x20, 0x00, 0x42, 0x01, 0x7c,
  0x20, 0x01, 0x41, 0x01, 0x6b, 0x10, 0x01, 0x20, 0x01, 0x6c, 0x05, 0x41,
  0x01, 0x0b, 0x0b, 0x15, 0x01, 0x01, 0x7f, 0x41, 0x05, 0x21, 0x00, 0x03,
  0x40, 0x42, 0x0d, 0x20, 0x00, 0x10, 0x01, 0x10, 0x00, 0x0c, 0x00, 0x0b,
  0x0b
};
unsigned int hello_world_wasm_len = 97;

volatile bool handelingInterrupt = false;
uint8_t ward_buff[100] = {0};

/**
 * (END) WARDUINO & WEB ASSEMBLY RELATED DECLARATIONS
 */

#define BLINK_GPIO GPIO_NUM_10

static const char *TAG = "uart_events";

/**
 * This example shows how to use the UART driver to handle UART interrupt.
 *
 * - Port: UART0
 * - Receive (Rx) buffer: on
 * - Transmit (Tx) buffer: off
 * - Flow control: off
 * - Event queue: on
 * - Pin assignment: TxD (default), RxD (default)
 */

#define EX_UART_NUM UART_NUM_0
/*!< Set the number of consecutive and identical characters received by receiver which defines a UART pattern*/
#define PATTERN_CHR_NUM (3) 

#define BUF_SIZE (1024)
#define RD_BUF_SIZE (BUF_SIZE)
static QueueHandle_t uart0_queue;

// Both definition are same and valid
// static uart_isr_handle_t *handle_console;
static intr_handle_t handle_console;

// Receive buffer to collect incoming data
uint8_t rxbuf[256];
// Register to collect data length
uint16_t urxlen;

#define NOTASK 0

void blink_task(void *pvParameter) {
  gpio_pad_select_gpio(BLINK_GPIO);

  /* Set the GPIO as a push/pull output */
  gpio_set_direction(BLINK_GPIO, GPIO_MODE_OUTPUT);

  while (1) {
    /* Blink off (output low) */
    gpio_set_level(BLINK_GPIO, 0);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    /* Blink on (output high) */
    gpio_set_level(BLINK_GPIO, 1);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}
/*
 * Define UART interrupt subroutine to ackowledge interrupt
 */
static void IRAM_ATTR uart_intr_handle(void *arg) {
  uint16_t rx_fifo_len, status;
  uint16_t i;
  uint8_t b;

  status = UART0.int_st.val;             // read UART interrupt Status
  rx_fifo_len = UART0.status.rxfifo_cnt; // read number of bytes in UART buffer  //CARLOS ALWAYS RECEIVES ONE BYTE MORE THAN I SEND
  size_t buff_len =  0;

  while (rx_fifo_len) {
    b = UART0.fifo.rw_byte; // read all bytes
    rxbuf[i++] = b;
    ward_buff[buff_len++] = b;
    rx_fifo_len--;
  }

    // after reading bytes from buffer clear UART interrupt status
  uart_clear_intr_status(EX_UART_NUM, UART_RXFIFO_FULL_INT_CLR | UART_RXFIFO_TOUT_INT_CLR);
  
  if (buff_len) {
    wac.handleInterrupt(buff_len, ward_buff);
  }
    


  // a test code or debug code to indicate UART receives successfully,
  // you can redirect received byte as echo also
  
  //uart_write_bytes(EX_UART_NUM, (const char *)"RX Done\n", 8); //use this to send some data
}
/*
 * main
 */
void app_main() {
  int ret;
  esp_log_level_set(TAG, ESP_LOG_INFO);

  /* Configure parameters of an UART driver,
   * communication pins and install the driver */
  uart_config_t uart_config = {.baud_rate = 115200,
                               .data_bits = UART_DATA_8_BITS,
                               .parity = UART_PARITY_DISABLE,
                               .stop_bits = UART_STOP_BITS_1,
                               .flow_ctrl = UART_HW_FLOWCTRL_DISABLE};

  ESP_ERROR_CHECK(uart_param_config(EX_UART_NUM, &uart_config));

  // Set UART log level
  esp_log_level_set(TAG, ESP_LOG_INFO);

  // Set UART pins (using UART0 default pins ie no changes.)
  ESP_ERROR_CHECK(uart_set_pin(EX_UART_NUM, UART_PIN_NO_CHANGE,
                               UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE,
                               UART_PIN_NO_CHANGE));

  // Install UART driver, and get the queue.
  ESP_ERROR_CHECK(
      uart_driver_install(EX_UART_NUM, BUF_SIZE * 2, 0, 0, NULL, 0));

  // release the pre registered UART handler/subroutine
  ESP_ERROR_CHECK(uart_isr_free(EX_UART_NUM));

  // register new UART subroutine //TODO Carlos
  ESP_ERROR_CHECK(uart_isr_register(EX_UART_NUM, uart_intr_handle, NULL,
                                    ESP_INTR_FLAG_IRAM, &handle_console));

  // enable RX interrupt
  ESP_ERROR_CHECK(uart_enable_rx_intr(EX_UART_NUM));
  Serial.begin(115200);
  Serial.println("Setup ok");
#if (NOTASK == 1)
  while (1) {
    vTaskDelay(1000);
  }
#else
  xTaskCreate(&blink_task, "blink_task", configMINIMAL_STACK_SIZE, NULL, 5,
              NULL);
#endif
}

void setup() {
  // put your setup code here, to run once:
  app_main();
}

void loop() {
  // put your main code here, to run repeatedly:
  Module* m = wac.load_module(hello_world_wasm, hello_world_wasm_len, {});
  printf("START\n\n"); 
  wac.run_module(m);
  printf("DONE\n\n");
}
