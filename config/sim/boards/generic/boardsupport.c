#include <support.h>
#include <generated/csr.h>


void __attribute__ ((externally_visible)) exit(int a) {
#ifdef CSR_SUPERVISOR_FINISH_ADDR
	supervisor_finish_write(1);
#endif
	while(1);
}


void
initialise_board (){

}

static unsigned int time;

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
	start_trigger (){
	timer0_en_write(0);
	timer0_load_write(0xFFFFFFFF);
	timer0_en_write(1);
}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
	stop_trigger (){
	timer0_update_value_write(1);
	timer0_update_value_write(0);
	uint32_t time = timer0_value_read();
	printf("Bench time:%u\n",0xFFFFFFFF-time);
	exit(1);
}

