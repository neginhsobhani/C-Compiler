#include <stdio.h>
int a , b , c , n ;
int temp_int_1 , temp_int_2 ;
int main()
{
a = 1;
b = 1;
n = 0;
if (n < 10) goto6;
goto16;
c = b;
temp_int_1 = a + b;
b = temp_int_1;
a = c;
temp_int_2 = n + 1;
n = temp_int_2;
printf("%d\n",n);
printf("%d\n",a);
goto4;
}
