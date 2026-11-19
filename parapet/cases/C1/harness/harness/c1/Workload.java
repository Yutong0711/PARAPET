package harness.c1;

import example.prefs.PrefsCodec;
import example.prefs.PrefsCodec.UserPrefs;
import java.lang.management.ManagementFactory;

/**
 * Workload driver for the legitimate path: a session save/restore round trip
 * (encode then decode) of typical preferences. Single thread, single process.
 *
 * Args: warmupRounds measuredRounds opsPerRound. Warm-up rounds are run and
 * discarded; the elapsed time of each measured round is reported in ns.
 */
public final class Workload {
    private Workload() {
    }

    static long round(UserPrefs p, int ops) throws Exception {
        long sink = 0;
        for (int i = 0; i < ops; i++) {
            String token = PrefsCodec.encode(p);
            UserPrefs q = PrefsCodec.decode(token);
            sink += token.length() + q.getRecentFiles().size() + q.getFontSize();
        }
        return sink;
    }

    public static void main(String[] args) throws Exception {
        int warmup = Integer.parseInt(args[0]);
        int measured = Integer.parseInt(args[1]);
        int ops = Integer.parseInt(args[2]);
        UserPrefs p = Samples.typical();
        long sink = 0;
        for (int r = 0; r < warmup; r++) {
            sink += round(p, ops);
        }
        com.sun.management.ThreadMXBean tmx =
                (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();
        long alloc0 = tmx.getCurrentThreadAllocatedBytes();
        StringBuilder rounds = new StringBuilder();
        for (int r = 0; r < measured; r++) {
            long t0 = System.nanoTime();
            sink += round(p, ops);
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
