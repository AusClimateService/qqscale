FC = ifort
NCFLAG = -I $(NETCDF_ROOT)/include
FFLAGS = -qopenmp -fpp -ftz -fp-model precise $(NCFLAG) -traceback
LIBS = -L $(NETCDF_ROOT)/lib -lnetcdf -lnetcdff

OBJ = qqscale.o readswitch.o netcdf_m.o

qqscale: $(OBJ)
	$(FC) -o qqscale $(FFLAGS) $(OBJ) $(LIBS)

clean:
	rm *.o *.mod qqscale
	
.SUFFIXES:.f90 .F90

.f90.o:
	$(FC) -c $(FFLAGS) $<
.F90.o:
	$(FC) -c $(FFLAGS) $<	
.f.o:
	$(FC) -c $(FFLAGS) $<
	
# Remove mod rule from Modula 2 so GNU make doesn't get confused
%.o : %.mod

qqscale.o : netcdf_m.o
