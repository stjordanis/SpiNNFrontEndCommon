package spiNNManClasses.Enums;

import java.util.HashMap;

public enum RunTimeError {

    NONE(0),
    RESET(1),
    UNDEF(2),
    SVC(3),
    PABT(4),
    DABT(5),
    IRQ(6),
    FIQ(7),
    VIC(8),
    ABORT(9),
    MALLOC(10),
    DIVBY0(11),
    EVENT(12),
    SWERR(13),
    IOBUF(14),
    ENABLE(15),
    NULL(16),
    PKT(17),
    TIMER(18),
    API(19),
    SARK_VERSRION_INCORRECT(20);

    private static final HashMap<Integer, RunTimeError> map = new HashMap<>();
    private final int value;

    RunTimeError(int value){
        this.value = value;
    }
    
    static {
        for (RunTimeError runTimeError : RunTimeError.values()) {
            map.put(RunTimeError.value, runTimeError);
        }
    }
    
    public static RunTimeError valueOf(int runTimeError) {
        return map.get(runTimeError);
    }

    public int getValue() {
        return this.value;
    }

    @Override
    public String toString() {
         return String.valueOf(this.value);
    }
}