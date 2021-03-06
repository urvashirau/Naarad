#ifndef RemoteCmd_h
#define RemoteCmd_h

// This file contains the information about the commands understood at
// the MCU on the remote sprinkler controller.
//
// Remote commands:
// ---------------
//
// The RFM_SEND commands to be followed by 4 arguments (all
// integers).  The first argument is a string "RFM_SEND" which 
// indicates to the Naarad sever on RPi that this has to be 
// sent via the RFM69 radio, not the OOK radio.
//
// The RFM is connected to the UNO and the server there (unoserver2)
// packs the 4 arguments into two integers of the RFM payload and
// radiates them as packets. The packet header contains the ID of the node
// sending it (the server UNO ID).  The NODE value (arg2 below) is the
// ID of the target receiver node.
//
// ASCII            Arg1     Arg2      Arg3               Arg4
//                Nibble1  Nibble0   Nibble1            Nibble0
// RFM_SEND        NODE      CMD       P1                 P0
//--------------------------------------------------------------------------------
// VALVE CLOSE       N        0       PORT          TIMEOUT in minutes (default 30min)
//
// VALVE OPEN        N        1       PORT          TIMEOUT in minutes (default 30min)
//
// VALVE SHUT        N        2       PORT          N/A
//
// Set RX TO         N        3        N/A          TIMEOUT in  sec. (default 3sec)
//
// Set TX interval   N        4      TO in sec.     Multiplier (default 1)
//                                   (default 60s)
//
// Set valve pulse   N        5     Multiplier     Pulse width in milli sec.
// width                                           (default 10ms)
//
// NOOP              N       255       N/A         N/A
//
//
// Cmd-0,1 (CLOSE,OPEN) raises the appropriate DIO pins to LOW/HIGH
// for 10ms (default) after which a SHUT commands is issued.
//
// Cmd-2 (SHUT) puts both the DIO pins connected to the port PORT of
// L9110s to LOW values.
//
// Cmd-3 (SET_RX_TO) sets the max. length of time for which the radio is
// in RX mode.  After this, it is assumed that there is nothing to
// receive and the radio goes to sleep mode.
//
// Cmd-4 (SET_TX_INT) sets the interval for which the remote unit is
// shut (the radio and the MCU in sleep mode).  This is the timescale
// on which the remote unit sends its sensor data and listens for
// commands from the server.  It is calculated as
//
//   for i=0; i<MULTIPLIER;i++) sleep(TO sec.);
//
// Cmd-5 (SET_VALVE_PULSE_WIDTH) sets the width of the pulse in time
// sent to the solenoid (via L9110s) by keeping the DIO pins to
// HIGH/LOW for this length of time.
//
// Cmd-255 (NOOP) does nothing. It is currently treated as an hint
// that there is nothing to receive for this node.


#define CODE_DONE 10

// Commands
#define CLOSE            0
#define OPEN             1
#define SHUT             2
// Commands to set various parameters. 
#define SET_RX_TO  3  
#define SET_TX_INT 4
#define SET_VALVE_PULSE_WIDTH 5 //The delay after CLOSE/OPEN commands

// The NOOP command.  This is the highest value possible.  And it is
// good to issue a NOOP command from the server.  That ensures that
// the remote radio is in the Rx mode for the minimum required time
// since it is shut down as soon as a command is received and ACK
// sent.
#define NOOP            255 

#endif
