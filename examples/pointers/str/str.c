#include <emscripten.h>

struct foo {
    long int a;
    long int b;
    long int c;
};

void EMSCRIPTEN_KEEPALIVE bar(struct foo * p, long int * v){
    *v = *v + p->a + p->b + p->c + 20;
}

int main(){
    struct foo my_foo;
    my_foo.a = 77;
    my_foo.b = 5;
    my_foo.c = 8;
    long int some_v = 44;
    bar(&my_foo, &some_v);
    return some_v + my_foo.a + my_foo.b +my_foo.c;
}
