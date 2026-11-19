package harness.c2;

import example.config.ConfigLoader;
import java.lang.management.ManagementFactory;
import java.util.Map;

/**
 * Workload driver for the legitimate path: loading a ~7 KB configuration
 * document. Single thread, single process.
 *
 * Args: warmupRounds measuredRounds opsPerRound. Warm-up rounds are run and
 * discarded; the elapsed time of each measured round is reported in ns.
 */
public final class Workload {
    private Workload() {
    }

    static long round(String xml, int ops) throws Exception {
        long sink = 0;
        for (int i = 0; i < ops; i++) {
            Map<String, String> m = ConfigLoader.load(xml);
            sink += m.size();
        }
        return sink;
    }

    public static void main(String[] args) throws Exception {
        int warmup = Integer.parseInt(args[0]);
        int measured = Integer.parseInt(args[1]);
        int ops = Integer.parseInt(args[2]);
        String xml = Docs.workload();
        long sink = 0;
        for (int r = 0; r < warmup; r++) {
            sink += round(xml, ops);
        }
        com.sun.management.ThreadMXBean tmx =
                (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();
        long alloc0 = tmx.getCurrentThreadAllocatedBytes();
        StringBuilder rounds = new StringBuilder();
        for (int r = 0; r < measured; r++) {
            long t0 = System.nanoTime();
            sink += round(xml, ops);
            long t1 = System.nanoTime();
            if (r > 0) {
                rounds.append(',');
            }
            rounds.append(t1 - t0);
        }
        long alloc1 = tmx.getCurrentThreadAllocatedBytes();
        double allocPerOp = (double) (alloc1 - alloc0) / ((double) measured * ops);
        System.out.println("PARAPET_WORKLOAD {\"warmup\":" + warmup + ",\"measured\":" + measured
                + ",\"ops\":" + ops + ",\"round_ns\":[" + rounds + "],\"alloc_bytes_per_op\":" + allocPerOp
                + ",\"sink\":" + sink + "}");
    }
}
