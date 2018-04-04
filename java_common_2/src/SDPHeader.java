public class SDPHeader{
    private final int destination_chip_x;
    private final int destination_chip_y;
    private final int destination_chip_p;
    private final int destination_port;
    private final int flags;
    private final int tag;
    private final int source_port;
    private final int source_cpu;
    private final int source_chip_x;
    private final int source_chip_y;
    private int length = 10;

    public SDPHeader(
            int destination_chip_x, int destination_chip_y,
            int destination_chip_p, int destination_port,
            int flags,
            int tag,
            int source_port,
            int source_cpu,
            int source_chip_x,
            int source_chip_y) {
        this.destination_chip_x = 0xFF & destination_chip_x;
        this.destination_chip_y = 0xFF & destination_chip_y;
        this.destination_chip_p = 0xFF & destination_chip_p;
        this.destination_port = 0xFF & destination_port;
        this.flags = 0xFF & flags;
        this.tag = 0xFF & tag;
        this.source_port = 0xFF & source_port;
        this.source_cpu = 0xFF & source_cpu;
        this.source_chip_x = 0xFF & source_chip_x;
        this.source_chip_y = 0xFF & source_chip_y;
        this.length = 10;
    }

    byte[] convert_byte_array(){
        int tmp;
        byte[] message_data = new byte[this.length];
        message_data[0] = 0;
        message_data[1] = 0;
        message_data[2] = (byte) this.flags;
        message_data[3] = (byte) this.tag;

        //Compose  Dest_port+cpu = 3 MSBs as port and 5 LSBs as cpu
        tmp = ((this.destination_port & 7) << 5)
                | (this.destination_chip_p & 31);
        message_data[4] = (byte) tmp;

        //Compose  Source_port+cpu = 3 MSBs as port and 5 LSBs as cpu
        tmp = ((this.source_port & 7) << 5) | (this.source_cpu & 31);
        message_data[5] = (byte) tmp;
        message_data[6] = (byte) this.destination_chip_y;
        message_data[7] = (byte) this.destination_chip_x;
        message_data[8] = (byte) this.source_chip_y;
        message_data[9] = (byte) this.source_chip_x;

        return message_data;
    }

    int length_in_bytes(){
        return this.length;
    }
}