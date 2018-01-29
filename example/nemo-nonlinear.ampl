var t2 binary;
var t3 binary;
var t1 binary;
minimize obj:t2*(1-0.25*((1-t3)
+(1-t3)
+(1-t3)))
+t3*(1-0.25*((1-t2)
+(1-t2)
+(1-t2)))
+t1*(1-0.25*(1));
subject to c1: t1+t3>=1;
subject to c2: t2+t3>=1;
subject to c3: t2>=1;
