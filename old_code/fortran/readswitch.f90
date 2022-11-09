! Conformal Cubic Atmospheric Model
    
! Copyright 2015 Commonwealth Scientific Industrial Research Organisation (CSIRO)
    
! This file is part of the Conformal Cubic Atmospheric Model (CCAM)
!
! CCAM is free software: you can redistribute it and/or modify
! it under the terms of the GNU General Public License as published by
! the Free Software Foundation, either version 3 of the License, or
! (at your option) any later version.
!
! CCAM is distributed in the hope that it will be useful,
! but WITHOUT ANY WARRANTY; without even the implied warranty of
! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
! GNU General Public License for more details.
!
! You should have received a copy of the GNU General Public License
! along with CCAM.  If not, see <http://www.gnu.org/licenses/>.

!------------------------------------------------------------------------------
    
!
! SUBROUTINES FOR READING COMMAND LINE SWITCHES.
!

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! This subroutine interprets switches (i.e., seperates filenames from
! switch arguments)
!

Subroutine readswitch(options,nopts)

Implicit None

Integer, intent(in) :: nopts
Character(len=*), dimension(nopts,2), intent(inout) :: options
Character*1024 buffer
Integer nswitch,status,lastswitch,newswitch,i
Integer locate,clen

!nswitch = nargs()
nswitch = command_argument_count() + 1

If (nswitch.EQ.1) then
  Call help()
End if

lastswitch=-1
Do i=1,nswitch-1
  !Call getarg(i,buffer,status)
  call get_command_argument(i,buffer,clen,status)
  
  newswitch=locate(buffer(1:clen),options(:,1),nopts)
  If (newswitch.NE.-1) then
    If (lastswitch.NE.-1) then
      Write(6,*) "ERROR: No value for switch "//options(lastswitch,1)
      call finishbanner
      Stop -1
    End if
  Else
    If (lastswitch.NE.-1) then
      options(lastswitch,2)=buffer(1:clen)
    Else
      ! Later - Non-switches are assumed to be filenames
      Write(6,*) "ERROR: No switch specified for value "//buffer
      call finishbanner
      Stop -1
    End if
  Endif
  lastswitch=newswitch
 
Enddo

If (newswitch.NE.-1) then
  Write(6,*) "ERROR: No value for switch "//options(newswitch,1)
  call finishbanner
  Stop -1
End If

Return
End

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! This function locates the chosen switch in the list
!

Integer Function locate(ser,list,n)

Implicit None

Integer, intent(in) :: n
Character(len=*), intent(in) :: ser
Character(len=*), dimension(n), intent(in) :: list
Integer i

locate=-1
Do i=1,n
  If (ser.EQ.list(i)) then
    locate=i
  End if
Enddo

Return
End

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! This function returns an option value
!

Character*1024 Function returnoption(flag,options,nopts)

Implicit None

Integer, intent(in) :: nopts
Character(len=*), dimension(nopts,2), intent(in) :: options
Character(len=*), intent(in) :: flag
Integer pos
Integer locate

pos=locate(flag,options(:,1),nopts)
returnoption=trim(options(pos,2))

Return
End

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! This subroutine reads the namelist
!

Subroutine procnml(num,name,maxnum)

Implicit None

Integer, intent(in) :: maxnum
Integer, intent(out) :: num
Character(len=*), dimension(1:maxnum), intent(in) :: name
Integer i,j
Logical blank

blank=.FALSE.
i=0
Do While (.NOT.blank)
  i=i+1
  If ((Ichar(name(i)(1:1)).EQ.32).OR.(Ichar(name(i)(1:1)).EQ.0)) Then
    blank=.TRUE.
  End if
  
  If (i.EQ.maxnum) Then
    Write(6,*) "ERROR: maxnum reached in namelist"
    call finishbanner
    Stop -1
  End If

End Do

num=i-1

If (num.EQ.0) Then
  Write(6,*) "ERROR: Zero elements in namelist"
  call finishbanner
  Stop -1
End If

Return
End
