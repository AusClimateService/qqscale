program qqscale

! This program calculates Quantile-Quantile scale data

implicit none

integer nopts
character(len=1024), dimension(:,:), allocatable :: options

! Start banner
write(6,*) 'qqscale - calculates Quantile-Quantile scaling data'

! Read switches
nopts=7
allocate (options(nopts,2))
options(:,1) = (/ '-i', '-o', '-m', '-v', '-a', '-b', '-c' /)
options(:,2) = ''

call readswitch(options,nopts)
call defaults(options,nopts)

call qqscale_mode(options,nopts)

deallocate(options)

write(6,*) "qqscale completed sucessfully"
call finishbanner

end

subroutine help()

implicit none

write(6,*)
write(6,*) "Usage:"
write(6,*) "  env OMP_NUM_THREADS=1 qqscale -i inputfile -o outputfile -m mode -v vname -a gcm_pd -b gcm_fut"
write(6,*)
write(6,*) "Options:"
write(6,*) "  -i inputfile  Input GCM/RCM filename"
write(6,*) "  -o outputfile Output filename"
write(6,*) "  -m mode       calcqq (default), mulqq, addqq"
write(6,*) "  -v vname      Variable to process"
write(6,*) "  -a gcm_pd     Quantile file for GCM present time-period (mode=scaleqq)"
write(6,*) "  -b gcm_fut    Quantile file for GCM future time-period (mode=scaleqq)"
write(6,*)
write(6,*) "Examples:"
write(6,*) "  qqscale -m calcqq -v tasmax -i tasmax_obs_2000.nc -o percentile_tasmax_obs_2000.nc"
write(6,*)
write(6,*) "  qqscale -m mulqq -v tasmax -i tasmax_obs_2000.nc -o scaled_tasmax_2090.nc"
write(6,*) "          -a percentile_tasmax_gcm_2000.nc -b percentile_tasmax_gcm_2090.nc"
write(6,*)
stop

return
end subroutine help

subroutine defaults(options,nopts)

integer, intent(in) :: nopts
character(len=*), dimension(nopts,2), intent(inout) :: options
integer locate
integer infile, outfile, mode, vname, qqa, qqb

infile=locate('-i',options(:,1),nopts)
if ( options(infile,2)=='' ) then
  write(6,*) "ERROR: No input filename specified"
  stop
end if

outfile=locate('-o',options(:,1),nopts)
if ( options(outfile,2)=='' ) then
  write(6,*) "ERROR: No output filename specified"
  stop
end if

mode=locate('-m',options(:,1),nopts)
if ( options(mode,2)=='' ) then
  options(mode,2)='calcqq'
end if

vname=locate('-v',options(:,1),nopts)
if ( options(vname,2)=='' ) then
  write(6,*) "ERROR: No variable name specified"
  stop
end if

if ( options(mode,2)=='mulqq' .or. options(mode,2)=='addqq' ) then
  qqa=locate('-a',options(:,1),nopts)
  if ( options(qqa,2)=='' ) then
    write(6,*) "ERROR: mode=scaleqq requires GCM present time-period quantile file"
    stop
  end if
  
  qqb=locate('-b',options(:,1),nopts)
  if ( options(qqb,2)=='' ) then
    write(6,*) "ERROR: mode=scaleqq requires GCM future time-period quantile file"
    stop
  end if
end if

return
end subroutine defaults

subroutine qqscale_mode(options,nopts)

implicit none

integer, intent(in) :: nopts
character(len=1024) returnoption
character(len=1024) infile, outfile, mode, vname, qqa, qqb
character(len=*), dimension(nopts,2), intent(in) :: options

infile=returnoption('-i',options,nopts)
outfile=returnoption('-o',options,nopts)
mode=returnoption('-m',options,nopts)
vname=returnoption('-v',options,nopts)
qqa=''
qqb=''

select case(mode)
  case('calcqq')
    write(6,*) "Calculate QQ from file"
    call qqscale_calcqq(infile,outfile,vname)
  case('mulqq','addqq')
    write(6,*) "Apply QQ to file"
    qqa=returnoption('-a',options,nopts)
    qqb=returnoption('-b',options,nopts)    
    call qqscale_scaleqq(infile,outfile,vname,qqa,qqb,mode)   
  case default
    write(6,*) "ERROR: Unknown mode ",trim(mode)
    stop
end select

return
end subroutine qqscale_mode

subroutine qqscale_calcqq(infile,outfile,vname)

use netcdf_m

implicit none

integer, parameter :: len_percentile = 101
integer i, j, tt
integer ierr
integer ncid_in, dim_longitude_in, dim_latitude_in, dim_time_in
integer len_longitude, len_latitude, len_time
integer longitudeid_in, latitudeid_in, timeid_in, varid_in
integer ncid_out
integer longitudeid_out, latitudeid_out, percentid_out, varid_out, meanid_out
integer, dimension(3) :: dimid_out
integer, dimension(3) :: start_in, count_in
integer, dimension(3) :: start_out, count_out
real, dimension(0:100) :: pout_loc
real, dimension(:), allocatable :: rlatitude, rlongitude, rpercentile
real, dimension(:), allocatable :: vin_loc
real, dimension(:,:), allocatable :: vin, vmean
real, dimension(:,:,:), allocatable :: pout
real(kind=8) sumd
character(len=*), intent(in) :: infile, outfile, vname
character(len=1024) lonname_in, latname_in, timeunit_in
character(len=1024) vstandard, vunits


! open input atmospheric file
write(6,*) "Opening ",trim(infile)
ierr = nf90_open(infile, nf_nowrite, ncid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot open ",trim(infile)
  stop
end if

! calculate dimensions
ierr = nf90_inq_dimid(ncid_in,'lon',dim_longitude_in)
lonname_in = "lon"
if ( ierr/=nf90_noerr ) then
  ierr = nf90_inq_dimid(ncid_in,'longitude',dim_longitude_in)
  lonname_in = "longitude"
end if
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate longitude dimension in ",trim(infile)
  stop
end if
ierr = nf90_inquire_dimension(ncid_in,dim_longitude_in,len=len_longitude)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate longitude dimension in ",trim(infile)
  stop
end if
ierr = nf90_inq_varid(ncid_in,trim(lonname_in),longitudeid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate lon variable in ",trim(infile)
  stop
end if


ierr = nf90_inq_dimid(ncid_in,'lat',dim_latitude_in)
latname_in = "lat"
if ( ierr/=nf90_noerr ) then
  ierr = nf90_inq_dimid(ncid_in,'latitude',dim_latitude_in)
  latname_in = "latitude"  
end if
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate latitude dimension in ",trim(infile)
  stop
end if
ierr = nf90_inquire_dimension(ncid_in,dim_latitude_in,len=len_latitude)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate latitude dimension in ",trim(infile)
  stop
end if
ierr = nf90_inq_varid(ncid_in,trim(latname_in),latitudeid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate lat variable in ",trim(infile)
  stop
end if


ierr = nf90_inq_dimid(ncid_in,'time',dim_time_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate time dimension in ",trim(infile)
  stop
end if
ierr = nf90_inquire_dimension(ncid_in,dim_time_in,len=len_time)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate time dimension in ",trim(infile)
  stop
end if
ierr = nf90_inq_varid(ncid_in,'time',timeid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate time variable in ",trim(infile)
  stop
end if

write(6,*) "Found dimensions ",len_longitude,len_latitude,len_time

ierr = nf90_inq_varid(ncid_in,vname,varid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate variable in ",trim(infile)
  stop
end if

ierr = nf90_get_att(ncid_in,timeid_in,"units",timeunit_in)
ierr = nf90_get_att(ncid_in,varid_in,"standard_name",vstandard)
ierr = nf90_get_att(ncid_in,varid_in,"units",vunits)


start_in(:) = 1
count_in(1) = len_longitude
count_in(2) = 1
count_in(3) = len_time

start_out(:) = 1
count_out(1) = len_longitude
count_out(2) = len_latitude
count_out(3) = len_percentile

! create output file
write(6,*) "Creating output file ",trim(outfile)
ierr = nf90_create(outfile, nf90_netcdf4, ncid_out)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot create output file ",trim(outfile)
  stop
end if

ierr = nf90_def_dim(ncid_out,"longitude",len_longitude,dimid_out(1))
ierr = nf90_def_var(ncid_out,"longitude",nf90_float,dimid_out(1),longitudeid_out)
ierr = nf90_put_att(ncid_out,longitudeid_out,"standard_name","longitude")
ierr = nf90_put_att(ncid_out,longitudeid_out,"axis","X")
ierr = nf90_put_att(ncid_out,longitudeid_out,"units","degrees_east")

ierr = nf90_def_dim(ncid_out,"latitude",len_latitude,dimid_out(2))
ierr = nf90_def_var(ncid_out,"latitude",nf90_float,dimid_out(2),latitudeid_out)
ierr = nf90_put_att(ncid_out,latitudeid_out,"standard_name","latitude")
ierr = nf90_put_att(ncid_out,latitudeid_out,"axis","Y")
ierr = nf90_put_att(ncid_out,latitudeid_out,"units","degrees_north")

ierr = nf90_def_dim(ncid_out,"percentile",len_percentile,dimid_out(3))
ierr = nf90_def_var(ncid_out,"percentile",nf90_float,dimid_out(3),percentid_out)
ierr = nf90_put_att(ncid_out,percentid_out,"standard_name","percentile")
ierr = nf90_put_att(ncid_out,percentid_out,"units","%")

ierr = nf90_def_var(ncid_out,vname,nf90_float,dimid_out(1:3),varid_out)
ierr = nf90_def_var_deflate(ncid_out,varid_out,1,1,1)
ierr = nf90_put_att(ncid_out,varid_out,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out,varid_out,"units",vunits)
ierr = nf90_put_att(ncid_out,varid_out,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out,varid_out,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out,"mean",nf90_float,dimid_out(1:2),meanid_out)
ierr = nf90_def_var_deflate(ncid_out,meanid_out,1,1,1)
ierr = nf90_put_att(ncid_out,meanid_out,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out,meanid_out,"units",vunits)
ierr = nf90_put_att(ncid_out,meanid_out,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out,meanid_out,"_FillValue",1.e20)

ierr = nf90_enddef(ncid_out)



allocate( rlatitude(len_latitude), rlongitude(len_longitude), rpercentile(0:100) )

! use start_out and count_out because the laitude can be read in
ierr = nf90_get_var(ncid_in,latitudeid_in,rlatitude,start=start_out(2:2),count=count_out(2:2))
ierr = nf90_get_var(ncid_in,longitudeid_in,rlongitude,start=start_in(1:1),count=count_in(1:1))

do i = 0,100
  rpercentile(i) = real(i)
end do  

ierr = nf90_put_var(ncid_out,longitudeid_out,rlongitude,start=start_out(1:1),count=count_out(1:1))
ierr = nf90_put_var(ncid_out,latitudeid_out,rlatitude,start=start_out(2:2),count=count_out(2:2))
ierr = nf90_put_var(ncid_out,percentid_out,rpercentile,start=start_out(3:3),count=count_out(3:3))

deallocate( rlatitude, rlongitude, rpercentile )



! prepare input and output arrays
write(6,*) "Allocating memory"
allocate( vin(len_longitude,len_time), vin_loc(len_time) )
allocate( vmean(len_longitude,len_latitude) )
allocate( pout(len_longitude,len_latitude,0:100) )

! loop over lat dimension
write(6,*) "Begin main latitude loop"
do j = 1,len_latitude
  if ( mod(j,10)==0 .or. j==len_latitude ) then
    write(6,*) "Processing latitude ",j,"/",len_latitude
  end if  


  ! load atmospheric data
  start_in(2) = j
  ierr = nf90_get_var(ncid_in,varid_in,vin,start=start_in(1:3),count=count_in(1:3))

  ! calculate percentile
!$OMP PARALLEL DO DEFAULT(NONE) SHARED(len_longitude,len_time,j,vin,vmean,pout) PRIVATE(i,tt,vin_loc,pout_loc,sumd)
  do i = 1,len_longitude
    vin_loc(:) = vin(i,:)  
    if ( all(abs(vin_loc)<1.e20) ) then
      sumd=0._8
      do tt=1,len_time
        sumd=sumd+real(vin_loc(tt),8)
      end do
      sumd=sumd/real(len_time,8)	
      vmean(i,j) = real(sumd)
      call pcalc( vin_loc, pout_loc, len_time )
      pout(i,j,0:100) = pout_loc  
    else
      vmean(i,j) = 1.e20
      pout(i,j,0:100) = 1.e20
    end if  
  end do
!$OMP END PARALLEL DO
      
end do
write(6,*) "Finish main latitude loop"

! fix missing values
where ( abs(pout)>1.e19 )
  pout = 1.e20
end where

! write percentile output file
write(6,*) "Write data to file"
ierr = nf90_put_var(ncid_out,varid_out,pout,start=start_out(1:3),count=count_out(1:3))
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot write to output file ",trim(outfile)
  write(6,*) "ierr ",ierr
  stop
end if
ierr = nf90_put_var(ncid_out,meanid_out,vmean,start=start_out(1:2),count=count_out(1:2))
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot write to output file ",trim(outfile)
  write(6,*) "ierr ",ierr
  stop
end if



! close input and output files
write(6,*) "Close netcdf files"
ierr = nf90_close(ncid_in)
ierr = nf90_close(ncid_out)

write(6,*) "Deallocate memory"
deallocate( vin, vin_loc, pout )
deallocate( vmean )

write(6,*) "qqscale - calcqq - completed sucessfully"

return
end subroutine qqscale_calcqq


subroutine pcalc( vin, pout, len_time )

implicit none

integer, intent(in) :: len_time
integer, parameter :: ngaps = 11
integer igap, i, j, gap
integer, dimension(ngaps) :: gaps
real, dimension(len_time), intent(inout) :: vin
real, dimension(0:100), intent(out) :: pout
real temp

gaps=(/ 7983, 3548, 1577, 701, 301, 132, 57, 23, 10, 4, 1 /)

do igap = 1,ngaps
  gap = gaps(igap)
  do i = gap, len_time-1
    temp = vin(i+1)
    j = i
    do while ( j>=gap .and. vin(max(j-gap+1,1))>temp )
      vin(j+1) = vin(j-gap+1)
      j = j - gap
    end do
    vin(j+1) = temp
  end do 
end do    


do i = 0,100
  j = nint(real(len_time-1)*real(i)/100.)+1
  pout(i) = vin(j)
end do  

return
end subroutine pcalc

subroutine qqscale_scaleqq(infile,outfile,vname,qqa,qqb,mode)

use netcdf_m

implicit none

integer, parameter :: len_percentile = 101
integer tt, i, j, pos_loc
integer ierr
integer ncid_in, dim_longitude_in, dim_latitude_in, dim_time_in
integer len_longitude, len_latitude, len_time
integer longitudeid_in, latitudeid_in, varid_in, timeid_in
integer ncid_out, ncid_qqa, ncid_out2
integer dim_longitude_qqa, dim_latitude_qqa
integer len_longitude_qqa, len_latitude_qqa
integer longitudeid_qqa, latitudeid_qqa, qqid_qqa, meanid_qqa
integer longitudeid_out, latitudeid_out, varid_out, timeid_out
integer longitudeid_out2, latitudeid_out2, varid_out2, timeid_out2
integer percentid_out2,meanid_out2,scaleid_out2
integer qqaid_out2, qqbid_out2
integer qqameanid_out2, qqbmeanid_out2, vmeanid_out2, scalemeanid_out2
integer, dimension(3) :: dimid_out, dimid_out2
integer, dimension(3) :: start_in, count_in
integer, dimension(3) :: start_qqa, count_qqa
integer, dimension(3) :: start_out, count_out
integer, dimension(3) :: start_out2, count_out2
real timer, vin1_loc, x, new_sfac
real, dimension(0:100) :: sfac_loc, pin_loc
real, dimension(:), allocatable :: vin_loc
real, dimension(:), allocatable :: rlatitude, rlongitude, rpercentile
real, dimension(:), allocatable :: platitude, plongitude
real, dimension(:,:), allocatable :: vin, vmean, qqamean, qqbmean, meanraw, scalemean
real, dimension(:,:,:), allocatable :: vout
real, dimension(:,:,:), allocatable :: qqaraw, qqain
real, dimension(:,:,:), allocatable :: qqbin
real, dimension(:,:,:), allocatable :: sfac
real, dimension(:,:,:), allocatable :: pin
real, dimension(:,:), allocatable :: meanchange
real(kind=8) sumd
character(len=*), intent(in) :: infile, outfile, vname, qqa, qqb, mode
character(len=1024) lonname_in, latname_in, outfile_sclpar
character(len=1024) timeunit_in, vstandard, vunits
character(len=1024) vcalendar

! open input atmospheric file
write(6,*) "Opening ",trim(infile)
ierr = nf90_open(infile, nf_nowrite, ncid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot open ",trim(infile)
  stop
end if

! calculate dimensions
ierr = nf90_inq_dimid(ncid_in,'lon',dim_longitude_in)
lonname_in = "lon"
if ( ierr/=nf90_noerr ) then
  ierr = nf90_inq_dimid(ncid_in,'longitude',dim_longitude_in)
  lonname_in = "longitude"
end if
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate longitude dimension in ",trim(infile)
  stop
end if
ierr = nf90_inquire_dimension(ncid_in,dim_longitude_in,len=len_longitude)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate longitude dimension in ",trim(infile)
  stop
end if
ierr = nf90_inq_varid(ncid_in,trim(lonname_in),longitudeid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate lon variable in ",trim(infile)
  stop
end if


ierr = nf90_inq_dimid(ncid_in,'lat',dim_latitude_in)
latname_in = "lat"
if ( ierr/=nf90_noerr ) then
  ierr = nf90_inq_dimid(ncid_in,'latitude',dim_latitude_in)
  latname_in = "latitude"  
end if
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate latitude dimension in ",trim(infile)
  stop
end if
ierr = nf90_inquire_dimension(ncid_in,dim_latitude_in,len=len_latitude)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate latitude dimension in ",trim(infile)
  stop
end if
ierr = nf90_inq_varid(ncid_in,trim(latname_in),latitudeid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate lat variable in ",trim(infile)
  stop
end if



ierr = nf90_inq_dimid(ncid_in,'time',dim_time_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate time dimension in ",trim(infile)
  stop
end if
ierr = nf90_inquire_dimension(ncid_in,dim_time_in,len=len_time)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate time dimension in ",trim(infile)
  stop
end if
ierr = nf90_inq_varid(ncid_in,'time',timeid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate time variable in ",trim(infile)
  stop
end if

write(6,*) "Found dimensions ",len_longitude,len_latitude,len_time

ierr = nf90_inq_varid(ncid_in,vname,varid_in)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot locate variable in ",trim(infile)
  stop
end if

ierr = nf90_get_att(ncid_in,timeid_in,"units",timeunit_in)
ierr = nf90_get_att(ncid_in,timeid_in,"calendar",vcalendar)
ierr = nf90_get_att(ncid_in,varid_in,"standard_name",vstandard)
ierr = nf90_get_att(ncid_in,varid_in,"units",vunits)


start_in(:) = 1
count_in(1) = len_longitude
count_in(2) = len_latitude
count_in(3) = 1

start_out(:) = 1
count_out(1) = len_longitude
count_out(2) = len_latitude
count_out(3) = 1

start_out2(:) = 1
count_out2(1) = len_longitude
count_out2(2) = len_latitude
count_out2(3) = len_percentile

! create output file
write(6,*) "Creating output file ",trim(outfile)
ierr = nf90_create(outfile, nf90_netcdf4, ncid_out)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot create output file ",trim(outfile)
  stop
end if

ierr = nf90_def_dim(ncid_out,"longitude",len_longitude,dimid_out(1))
ierr = nf90_def_var(ncid_out,"longitude",nf90_float,dimid_out(1),longitudeid_out)
ierr = nf90_put_att(ncid_out,longitudeid_out,"standard_name","longitude")
ierr = nf90_put_att(ncid_out,longitudeid_out,"axis","X")
ierr = nf90_put_att(ncid_out,longitudeid_out,"units","degrees_east")

ierr = nf90_def_dim(ncid_out,"latitude",len_latitude,dimid_out(2))
ierr = nf90_def_var(ncid_out,"latitude",nf90_float,dimid_out(2),latitudeid_out)
ierr = nf90_put_att(ncid_out,latitudeid_out,"standard_name","latitude")
ierr = nf90_put_att(ncid_out,latitudeid_out,"axis","Y")
ierr = nf90_put_att(ncid_out,latitudeid_out,"units","degrees_north")

ierr = nf90_def_dim(ncid_out,"time",nf90_unlimited,dimid_out(3))
ierr = nf90_def_var(ncid_out,"time",nf90_float,dimid_out(3),timeid_out)
ierr = nf90_put_att(ncid_out,timeid_out,"standard_name","time")
ierr = nf90_put_att(ncid_out,timeid_out,"axis","T")
ierr = nf90_put_att(ncid_out,timeid_out,"units",timeunit_in)
ierr = nf90_put_att(ncid_out,timeid_out,"calendar",vcalendar)

ierr = nf90_def_var(ncid_out,vname,nf90_float,dimid_out(1:3),varid_out)
ierr = nf90_def_var_deflate(ncid_out,varid_out,1,1,1)
ierr = nf90_put_att(ncid_out,varid_out,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out,varid_out,"units",vunits)
ierr = nf90_put_att(ncid_out,varid_out,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out,varid_out,"_FillValue",1.e20)


ierr = nf90_enddef(ncid_out)



allocate( rlatitude(len_latitude), rlongitude(len_longitude) )

ierr = nf90_get_var(ncid_in,longitudeid_in,rlongitude,start=start_in(1:1),count=count_in(1:1))
ierr = nf90_get_var(ncid_in,latitudeid_in,rlatitude,start=start_in(2:2),count=count_in(2:2))

ierr = nf90_put_var(ncid_out,longitudeid_out,rlongitude,start=start_out(1:1),count=count_out(1:1))
ierr = nf90_put_var(ncid_out,latitudeid_out,rlatitude,start=start_out(2:2),count=count_out(2:2))


! create 2nd output file
outfile_sclpar = trim(outfile)//".sclpar.nc"
write(6,*) "Creating output file ",trim(outfile_sclpar)
ierr = nf90_create(outfile_sclpar, nf90_netcdf4, ncid_out2)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot create scale output ",trim(outfile_sclpar)
  write(6,*) nf90_strerror(ierr)  
  stop
end if

ierr = nf90_def_dim(ncid_out2,"longitude",len_longitude,dimid_out2(1))
ierr = nf90_def_var(ncid_out2,"longitude",nf90_float,dimid_out2(1),longitudeid_out2)
ierr = nf90_put_att(ncid_out2,longitudeid_out2,"standard_name","longitude")
ierr = nf90_put_att(ncid_out2,longitudeid_out2,"axis","X")
ierr = nf90_put_att(ncid_out2,longitudeid_out2,"units","degrees_east")

ierr = nf90_def_dim(ncid_out2,"latitude",len_latitude,dimid_out2(2))
ierr = nf90_def_var(ncid_out2,"latitude",nf90_float,dimid_out2(2),latitudeid_out2)
ierr = nf90_put_att(ncid_out2,latitudeid_out2,"standard_name","latitude")
ierr = nf90_put_att(ncid_out2,latitudeid_out2,"axis","Y")
ierr = nf90_put_att(ncid_out2,latitudeid_out2,"units","degrees_north")

ierr = nf90_def_dim(ncid_out2,"percentile",len_percentile,dimid_out2(3))
ierr = nf90_def_var(ncid_out2,"percentile",nf90_float,dimid_out2(3),percentid_out2)
ierr = nf90_put_att(ncid_out2,percentid_out2,"standard_name","percentile")
ierr = nf90_put_att(ncid_out2,percentid_out2,"units","%")

ierr = nf90_def_var(ncid_out2,vname,nf90_float,dimid_out2(1:3),varid_out2)
ierr = nf90_def_var_deflate(ncid_out2,varid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,varid_out2,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out2,varid_out2,"units",vunits)
ierr = nf90_put_att(ncid_out2,varid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,varid_out2,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out2,"percentilechange",nf90_float,dimid_out2(1:3),scaleid_out2)
ierr = nf90_def_var_deflate(ncid_out2,scaleid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,scaleid_out2,"standard_name",vstandard)
select case(mode)
  case('mulqq')
    ierr = nf90_put_att(ncid_out2,scaleid_out2,"units",'frac')
  case('addqq')
    ierr = nf90_put_att(ncid_out2,scaleid_out2,"units",vunits)
end select
ierr = nf90_put_att(ncid_out2,scaleid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,scaleid_out2,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out2,"meanchange",nf90_float,dimid_out2(1:2),meanid_out2)
ierr = nf90_def_var_deflate(ncid_out2,meanid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,meanid_out2,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out2,meanid_out2,"units",'frac')
ierr = nf90_put_att(ncid_out2,meanid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,meanid_out2,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out2,"GCMA",nf90_float,dimid_out2(1:3),qqaid_out2)
ierr = nf90_def_var_deflate(ncid_out2,qqaid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,qqaid_out2,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out2,qqaid_out2,"units",vunits)
ierr = nf90_put_att(ncid_out2,qqaid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,qqaid_out2,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out2,"GCMB",nf90_float,dimid_out2(1:3),qqbid_out2)
ierr = nf90_def_var_deflate(ncid_out2,qqbid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,qqbid_out2,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out2,qqbid_out2,"units",vunits)
ierr = nf90_put_att(ncid_out2,qqbid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,qqbid_out2,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out2,"GCMAMEAN",nf90_float,dimid_out2(1:2),qqameanid_out2)
ierr = nf90_def_var_deflate(ncid_out2,qqameanid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,qqameanid_out2,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out2,qqameanid_out2,"units",vunits)
ierr = nf90_put_att(ncid_out2,qqameanid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,qqameanid_out2,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out2,"GCMBMEAN",nf90_float,dimid_out2(1:2),qqbmeanid_out2)
ierr = nf90_def_var_deflate(ncid_out2,qqbmeanid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,qqbmeanid_out2,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out2,qqbmeanid_out2,"units",vunits)
ierr = nf90_put_att(ncid_out2,qqbmeanid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,qqbmeanid_out2,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out2,"OBSMEAN",nf90_float,dimid_out2(1:2),vmeanid_out2)
ierr = nf90_def_var_deflate(ncid_out2,vmeanid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,vmeanid_out2,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out2,vmeanid_out2,"units",vunits)
ierr = nf90_put_att(ncid_out2,vmeanid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,vmeanid_out2,"_FillValue",1.e20)

ierr = nf90_def_var(ncid_out2,"SCALEMEAN",nf90_float,dimid_out2(1:2),scalemeanid_out2)
ierr = nf90_def_var_deflate(ncid_out2,scalemeanid_out2,1,1,1)
ierr = nf90_put_att(ncid_out2,scalemeanid_out2,"standard_name",vstandard)
ierr = nf90_put_att(ncid_out2,scalemeanid_out2,"units",vunits)
ierr = nf90_put_att(ncid_out2,scalemeanid_out2,"missing_value",1.e20)
ierr = nf90_put_att(ncid_out2,scalemeanid_out2,"_FillValue",1.e20)

ierr = nf90_enddef(ncid_out2)


allocate( rpercentile(0:100) )

do i = 0,100
  rpercentile(i) = real(i)
end do  

ierr = nf90_put_var(ncid_out2,longitudeid_out2,rlongitude,start=start_out(1:1),count=count_out(1:1))
ierr = nf90_put_var(ncid_out2,latitudeid_out2,rlatitude,start=start_out(2:2),count=count_out(2:2))
ierr = nf90_put_var(ncid_out2,percentid_out2,rpercentile,start=start_out(3:3),count=count_out(3:3))

deallocate( rpercentile )


! Read percentile file A

write(6,*) "Opening ",trim(qqa)
ierr = nf90_open(qqa, nf_nowrite, ncid_qqa)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot open ",trim(qqa)
  stop -1
end if

! calculate dimensions
ierr = nf90_inq_dimid(ncid_qqa,'longitude',dim_longitude_qqa)
ierr = nf90_inquire_dimension(ncid_qqa,dim_longitude_qqa,len=len_longitude_qqa)
ierr = nf90_inq_varid(ncid_qqa,'longitude',longitudeid_qqa)
ierr = nf90_inq_dimid(ncid_qqa,'latitude',dim_latitude_qqa)
ierr = nf90_inquire_dimension(ncid_qqa,dim_latitude_qqa,len=len_latitude_qqa)
ierr = nf90_inq_varid(ncid_qqa,'latitude',latitudeid_qqa)

ierr = nf90_inq_varid(ncid_qqa,vname,qqid_qqa)
ierr = nf90_inq_varid(ncid_qqa,"mean",meanid_qqa)

start_qqa(:) = 1
count_qqa(1) = len_longitude_qqa
count_qqa(2) = len_latitude_qqa
count_qqa(3) = len_percentile

write(6,*) "Found dimensions ",len_longitude_qqa,len_latitude_qqa,len_percentile

allocate( platitude(len_latitude_qqa), plongitude(len_longitude_qqa) )
allocate( qqaraw(len_longitude_qqa,len_latitude_qqa,0:100) )
allocate( qqain(len_longitude,len_latitude,0:100) )
allocate( meanraw(len_longitude_qqa,len_latitude_qqa) )
allocate( qqamean(len_longitude,len_latitude) )

! load percentile data
write(6,*) "Reading ",trim(qqa)
ierr = nf90_get_var(ncid_qqa,longitudeid_qqa,plongitude,start=start_qqa(1:1),count=count_qqa(1:1))
ierr = nf90_get_var(ncid_qqa,latitudeid_qqa,platitude,start=start_qqa(2:2),count=count_qqa(2:2))
ierr = nf90_get_var(ncid_qqa,qqid_qqa,qqaraw,start=start_qqa(1:3),count=count_qqa(1:3))
ierr = nf90_get_var(ncid_qqa,meanid_qqa,meanraw,start=start_qqa(1:2),count=count_qqa(1:2))

! Interpolate percentile file
write(6,*) "Interpolating ",trim(qqa)
call bilinear(qqaraw,qqain,plongitude,platitude,rlongitude,rlatitude, &
              len_longitude_qqa,len_latitude_qqa,len_longitude,len_latitude,101)
call bilinear(meanraw,qqamean,plongitude,platitude,rlongitude,rlatitude, &
              len_longitude_qqa,len_latitude_qqa,len_longitude,len_latitude,1)
deallocate( qqaraw, plongitude, platitude )
deallocate( meanraw )


! Read percentile file B

write(6,*) "Opening ",trim(qqb)
ierr = nf90_open(qqb, nf_nowrite, ncid_qqa)
if ( ierr/=nf90_noerr ) then
  write(6,*) "ERROR: Cannot open ",trim(qqb)
  stop -1
end if

! calculate dimensions
ierr = nf90_inq_dimid(ncid_qqa,'longitude',dim_longitude_qqa)
ierr = nf90_inquire_dimension(ncid_qqa,dim_longitude_qqa,len=len_longitude_qqa)
ierr = nf90_inq_varid(ncid_qqa,'longitude',longitudeid_qqa)
ierr = nf90_inq_dimid(ncid_qqa,'latitude',dim_latitude_qqa)
ierr = nf90_inquire_dimension(ncid_qqa,dim_latitude_qqa,len=len_latitude_qqa)
ierr = nf90_inq_varid(ncid_qqa,'latitude',latitudeid_qqa)

ierr = nf90_inq_varid(ncid_qqa,vname,qqid_qqa)
ierr = nf90_inq_varid(ncid_qqa,"mean",meanid_qqa)

start_qqa(:) = 1
count_qqa(1) = len_longitude_qqa
count_qqa(2) = len_latitude_qqa
count_qqa(3) = 101

write(6,*) "Found dimensions ",len_longitude_qqa,len_latitude_qqa,len_percentile

allocate( platitude(len_latitude_qqa), plongitude(len_longitude_qqa) )
allocate( qqaraw(len_longitude_qqa,len_latitude_qqa,0:100) )
allocate( qqbin(len_longitude,len_latitude,0:100) )
allocate( meanraw(len_longitude_qqa,len_latitude_qqa) )
allocate( qqbmean(len_longitude,len_latitude) )

! load percentile data
write(6,*) "Reading ",trim(qqb)
ierr = nf90_get_var(ncid_qqa,longitudeid_qqa,plongitude,start=start_qqa(1:1),count=count_qqa(1:1))
ierr = nf90_get_var(ncid_qqa,latitudeid_qqa,platitude,start=start_qqa(2:2),count=count_qqa(2:2))
ierr = nf90_get_var(ncid_qqa,qqid_qqa,qqaraw,start=start_qqa(1:3),count=count_qqa(1:3))
ierr = nf90_get_var(ncid_qqa,meanid_qqa,meanraw,start=start_qqa(1:2),count=count_qqa(1:2))

! Interpolate percentile file
write(6,*) "Interpolating ",trim(qqb)
call bilinear(qqaraw,qqbin,plongitude,platitude,rlongitude,rlatitude, &
              len_longitude_qqa,len_latitude_qqa,len_longitude,len_latitude,101)
call bilinear(meanraw,qqbmean,plongitude,platitude,rlongitude,rlatitude, &
              len_longitude_qqa,len_latitude_qqa,len_longitude,len_latitude,1)
deallocate( qqaraw, plongitude, platitude )
deallocate( meanraw )

deallocate( rlongitude, rlatitude )

! Calculate inflation
allocate( sfac(len_longitude,len_latitude,0:100) )
select case(mode)
  case('mulqq')
    do i = 0,100
      where ( abs(qqbin(:,:,i))<1.e19 .and. abs(qqain(:,:,i))<1.e19 )
        sfac(:,:,i) = max(qqbin(:,:,i),0.)/max(qqain(:,:,i),1.e-10)
      elsewhere
        sfac(:,:,i) = 1.e20
      end where
    end do
  case('addqq')  
    do i = 0,100
      where ( abs(qqbin(:,:,i))<1.e19 .and. abs(qqain(:,:,i))<1.e19 )
        sfac(:,:,i) = qqbin(:,:,i)-qqain(:,:,i)
      elsewhere
        sfac(:,:,i) = 1.e20
      end where
    end do
  case default
    write(6,*) "ERROR: Unknown mode ",trim(mode)
    stop
end select




! Calculate percentile from infile
write(6,*) "Calculating percentile from ",trim(infile)

start_in(:) = 1
count_in(1) = len_longitude
count_in(2) = 1
count_in(3) = len_time

allocate( pin(len_longitude,len_latitude,0:100) )
allocate( vin(len_longitude,len_time), vin_loc(len_time) )
allocate( vmean(len_longitude,len_latitude) )

do j = 1,len_latitude
  if ( mod(j,10)==0 .or. j==len_latitude ) then
    write(6,*) "Processing latitude ",j,"/",len_latitude
  end if  

  ! load atmospheric data
  start_in(2) = j
  ierr = nf90_get_var(ncid_in,varid_in,vin,start=start_in(1:3),count=count_in(1:3))

  ! calculate percentile
!$OMP PARALLEL DO DEFAULT(NONE) SHARED(len_longitude,len_time,j,vin,vmean,pin) PRIVATE(i,tt,vin_loc,pin_loc,sumd)
  do i = 1,len_longitude
    vin_loc(:) = vin(i,:)
    if ( all(abs(vin_loc)<1.e20) ) then
      sumd=0._8
      do tt=1,len_time
        sumd=sumd+real(vin_loc(tt),8)
      end do
      sumd=sumd/real(len_time,8)	
      vmean(i,j) = real(sumd)
      call pcalc( vin_loc, pin_loc, len_time )
      pin(i,j,0:100) = pin_loc  
    else
      vmean(i,j) = 1.e20
      pin(i,j,0:100) = 1.e20
    end if     
  end do
!$OMP END PARALLEL DO
      
end do

deallocate( vin, vin_loc )


! prepare input and output arrays
allocate( vin(len_longitude,len_latitude) )
allocate( vout(len_longitude,len_latitude,len_time) )

start_in(:) = 1
count_in(1) = len_longitude
count_in(2) = len_latitude
count_in(3) = 1


! loop over time dimension
write(6,*) "Begin main time loop"
do tt = 1,len_time
  if ( mod(tt,10)==0 .or. tt==len_time ) then
    write(6,*) "Processing time-step ",tt,"/",len_time
  end if  


  ! load atmospheric data
  start_in(3) = tt
  ierr = nf90_get_var(ncid_in,varid_in,vin,start=start_in(1:3),count=count_in(1:3))

    
  ! scale quantile
  select case(mode)
    case('mulqq')
!$OMP PARALLEL DO DEFAULT(NONE) SHARED(len_latitude,len_longitude,vin,vout,sfac,pin,tt) PRIVATE(i,j,vin1_loc,sfac_loc,pin_loc,pos_loc,x,new_sfac)
      do j = 1,len_latitude
        do i = 1,len_longitude
          sfac_loc(:) = sfac(i,j,:)
          pin_loc(:) = pin(i,j,:)
          if ( all(abs(sfac_loc)<1.e19) .and. all(abs(pin_loc)<1.e19) ) then
            vin1_loc = vin(i,j)
            call findpercentile( vin1_loc, pin_loc, pos_loc )
            pos_loc = min( pos_loc, 99 )
            x = ( vin1_loc - pin_loc(pos_loc) ) / max( pin_loc(pos_loc+1) - pin_loc(pos_loc), 1.e-10 )
            new_sfac = (1.-x)*sfac_loc(pos_loc) + x*sfac_loc(pos_loc+1)
            vin1_loc = vin1_loc*new_sfac
            vout(i,j,tt) = vin1_loc
          else
            vout(i,j,tt) = 1.e20
          end if
        end do
      end do    
!$OMP END PARALLEL DO
    case('addqq')
!$OMP PARALLEL DO DEFAULT(NONE) SHARED(len_latitude,len_longitude,vin,vout,sfac,pin,tt) PRIVATE(i,j,vin1_loc,sfac_loc,pin_loc,pos_loc,x,new_sfac)
      do j = 1,len_latitude
        do i = 1,len_longitude
          sfac_loc(:) = sfac(i,j,:)
          pin_loc(:) = pin(i,j,:)
          if ( all(abs(sfac_loc)<1.e19) .and. all(abs(pin_loc)<1.e19) ) then
            vin1_loc = vin(i,j)
            call findpercentile( vin1_loc, pin_loc, pos_loc )
            pos_loc = min( pos_loc, 99 )
            x = ( vin1_loc - pin_loc(pos_loc) ) / max( pin_loc(pos_loc+1) - pin_loc(pos_loc), 1.e-10 )
            new_sfac = (1.-x)*sfac_loc(pos_loc) + x*sfac_loc(pos_loc+1)
            vin1_loc = vin1_loc + new_sfac
            vout(i,j,tt) = vin1_loc
          else
            vout(i,j,tt) = 1.e20
          end if
        end do
      end do    
!$OMP END PARALLEL DO
    case default
      write(6,*) "ERROR: Unknown mode ",trim(mode)
      stop
  end select
  
end do

write(6,*) "Rescaling average"
allocate( scalemean(len_longitude,len_latitude) )
do j = 1,len_latitude
  do i = 1,len_longitude
    if ( all(abs(vout(i,j,:))<1.e20) ) then
      sumd=0._8
      do tt=1,len_time
        sumd=sumd+real(vout(i,j,tt),8)
      end do
      sumd=sumd/real(len_time,8)	
      scalemean(i,j) = real(sumd)    
    else
      scalemean(i,j) = 1.e20
    end if
  end do
end do

if ( any(qqamean==0.) ) then
  write(6,*) "ERROR: zero found in mean of ",trim(qqa)
  stop
end if
if ( any(scalemean==0.) ) then
  write(6,*) "ERROR: zero found in mean on ",trim(infile)
  stop
end if

allocate( meanchange(len_longitude,len_latitude) )

select case(mode)
  case('mulqq')
    where ( abs(qqamean)<1.e20 .and. abs(qqbmean)<1.e20 .and. &
            abs(vmean)<1.e20 .and. abs(scalemean)<1.e20 )
      meanchange=qqbmean(:,:)/qqamean(:,:)*vmean(:,:)/scalemean(:,:)	  
    elsewhere
      meanchange = 1.e20
    end where  
  case('addqq')
    where ( abs(qqamean)<1.e20 .and. abs(qqbmean)<1.e20 .and. &
            abs(vmean)<1.e20 .and. abs(scalemean)<1.e20 )
      meanchange=qqbmean(:,:)-qqamean(:,:)+vmean(:,:)-scalemean(:,:)	  
    elsewhere
      meanchange = 1.e20
    end where  
end select    
    

do tt = 1,len_time
  if ( mod(tt,10)==0 .or. tt==len_time ) then
    write(6,*) "Rescale time-step ",tt,"/",len_time
  end if  

  start_in(3) = tt
  ierr = nf90_get_var(ncid_in,timeid_in,timer,start=start_in(3:3))
  
  
  select case(mode)
    case('mulqq')
      where ( abs(vout(:,:,tt))<1.e20 .and.abs(meanchange)<1.e20 )
        vout(:,:,tt) = vout(:,:,tt)*meanchange
      elsewhere
        vout(:,:,tt) = 1.e20
      end where  
    case('addqq')
      where ( abs(vout(:,:,tt))<1.e20 .and.abs(meanchange)<1.e20 )
        vout(:,:,tt) = vout(:,:,tt) + meanchange
      elsewhere
        vout(:,:,tt) = 1.e20
      end where  
  end select  
  
  ! write scaled obs to output file
  start_out(3) = tt
  ierr = nf90_put_var(ncid_out,timeid_out,timer,start=start_out(3:3))
  ierr = nf90_put_var(ncid_out,varid_out,vout(:,:,tt),start=start_out(1:3),count=count_out(1:3))

end do
write(6,*) "Finish main time loop"

write(6,*) "Write scale and mean values"

!do i=0,100
!print *,"pin  ",i,minval(pin(:,:,i)),maxval(pin(:,:,i))
!print *,"sfac ",i,minval(sfac(:,:,i)),maxval(sfac(:,:,i))
!end do

ierr = nf90_put_var(ncid_out2,varid_out2,pin,start=start_out2(1:3),count=count_out2(1:3))
ierr = nf90_put_var(ncid_out2,scaleid_out2,sfac,start=start_out2(1:3),count=count_out2(1:3))
ierr = nf90_put_var(ncid_out2,meanid_out2,meanchange,start=start_out2(1:2),count=count_out2(1:2))

ierr = nf90_put_var(ncid_out2,qqaid_out2,qqain,start=start_out2(1:3),count=count_out2(1:3))
ierr = nf90_put_var(ncid_out2,qqbid_out2,qqbin,start=start_out2(1:3),count=count_out2(1:3))

ierr = nf90_put_var(ncid_out2,qqameanid_out2,qqamean,start=start_out2(1:2),count=count_out2(1:2))
ierr = nf90_put_var(ncid_out2,qqbmeanid_out2,qqbmean,start=start_out2(1:2),count=count_out2(1:2))
ierr = nf90_put_var(ncid_out2,vmeanid_out2,vmean,start=start_out2(1:2),count=count_out2(1:2))
ierr = nf90_put_var(ncid_out2,scalemeanid_out2,scalemean,start=start_out2(1:2),count=count_out2(1:2))


! close input and output files
write(6,*) "Close netcdf files"
ierr = nf90_close(ncid_in)
ierr = nf90_close(ncid_out)
ierr = nf90_close(ncid_out2)

write(6,*) "Deallocate memory"
deallocate( vin, vout )
deallocate( vmean )
deallocate( meanchange, pin, sfac )
deallocate( qqain, qqbin )


write(6,*) "qqscale - scaleqq - completed sucessfully"

return
end subroutine qqscale_scaleqq

subroutine findpercentile( vin, pin, pos )

implicit none

integer, intent(out) :: pos
integer i, imin, imax, itest
real, intent(in) :: vin
real, dimension(0:100), intent(in) :: pin

imin = 0
imax = 100
do while ( imax - imin > 1 )
  itest = int(0.5*(real(imin)+real(imax)))
  if ( vin>=pin(itest) ) then
    imin = itest
  else
    imax = itest
  end if  
end do

pos = imin

return
end subroutine findpercentile

subroutine bilinear(datin,datout,lonin,latin,lonout,latout,nxin,nyin,nxout,nyout,nsize)

implicit none

integer, intent(in) :: nxin, nyin
integer, intent(in) :: nxout, nyout
integer, intent(in) :: nsize
integer k, i, j, ii, jj, iip1, ia, jb
integer iinear, jjnear
real, dimension(nxin), intent(in) :: lonin
real, dimension(nyin), intent(in) :: latin
real, dimension(nxout), intent(in) :: lonout
real, dimension(nyout), intent(in) :: latout
real, dimension(nxin,nyin,1:nsize), intent(in) :: datin
real, dimension(nxout,nyout,1:nsize), intent(out) :: datout
real b, c, d, sx, sy, dx

do j = 1,nyout
  jj = -1
  do jb = 1,nyin-1
    if ( (latin(jb+1)-latout(j))*(latin(jb)-latout(j))<=0. ) then
      jj = jb
      exit
    end if  
  end do
  if ( jj<1 ) then
    write(6,*) "ERROR: Cannot find valid latitude for interpolation"
    write(6,*) "This might be because the input domain is larger than the"
    write(6,*) "GCM domain"
    stop
  end if    
  sy = ( latout(j) - latin(jj) ) / ( latin(jj+1) - latin(jj) )
  do i = 1,nxout
    ii = -1
    do ia = 1,nxin-1
      iip1 = ia + 1
      if ( iip1>nxin ) iip1 = 1
      sx = lonin(iip1)-lonout(i)
      dx = lonin(ia)-lonout(i)
      if ( sx > 180. ) sx = sx - 360.
      if ( sx < -180. ) sx = sx + 360.
      if ( dx > 180. ) dx = dx - 360.
      if ( dx < -180. ) dx = dx + 360. 
      if ( sx*dx<=0. ) then
        ii = ia
	exit
      end if
    end do
    if ( ii<1 ) then
      write(6,*) "ERROR: Cannot find valid longitude for interpolation"
      write(6,*) "This might be because the input domain is larger than the"
      write(6,*) "GCM domain"
      stop
    end if  
    iip1 = ii + 1
    if ( iip1>nxin ) iip1 = 1
    sx = ( lonout(i) - lonin(ii) )
    dx = ( lonin(iip1) - lonin(ii) )
    if ( sx > 180. ) sx = sx - 360.
    if ( sx < -180. ) sx = sx + 360.
    if ( dx > 180. ) dx = dx - 360.
    if ( dx < -180. ) dx = dx + 360.
    sx = sx/dx
    if ( nint(sx)==0 ) then
      iinear = ii
    else
      iinear = iip1
    end if
    jjnear = jj + nint(sy)
    do k = 1,nsize
      if ( abs(datin(ii,jj,k))<1.e19 .and. abs(datin(iip1,jj,k))<1.e19 .and. &
           abs(datin(ii,jj+1,k))<1.e19 .and. abs(datin(iip1,jj+1,k))<1.e19 ) then
        d = datin(iip1,jj+1,k)-datin(ii,jj+1,k)-datin(iip1,jj,k)+datin(ii,jj,k)
        b = datin(iip1,jj,k)-datin(ii,jj,k)
        c = datin(ii,jj+1,k)-datin(ii,jj,k)
        datout(i,j,k) = datin(ii,jj,k) + b*sx + c*sy + d*sx*sy
      else if ( abs(datin(iinear,jjnear,k))<1.e19 ) then	
	datout(i,j,k) = datin(iinear,jjnear,k)
      else
        datout(i,j,k) = 1.e20
      end if  
    end do  
  end do
end do    

return
end subroutine bilinear

subroutine finishbanner

implicit none

! End banner
write(6,*) "=============================================================================="
write(6,*) "Finished qqscale"
write(6,*) "=============================================================================="

return
end







