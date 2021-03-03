#include <emscripten.h>

struct fact {
		int res;
		int inp;
};
/* int fact(int v, struct fact *f) { */

int EMSCRIPTEN_KEEPALIVE fact(int v, struct fact *f) {
		if(v == f->inp){
				f->res = v;
				return fact(v - 1, f);
		}
		else if(v > 1) {
				f->res = f->res * v;
				return fact(v - 1, f);
		}
		else{
			return 1;
		}
}

int main(){
		struct fact f;
		int r;
		while(1){
				int inp = 5;
				f.inp = inp;
				f.res = inp;
				r = fact(inp, &f);
		}
    return f.res;
}
