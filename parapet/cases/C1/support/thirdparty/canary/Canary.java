package thirdparty.canary;

/**
 * Harmless canary. Stands in for the side effect of a deserialization gadget:
 * it only flips a static flag inside the JVM that runs the check. It performs
 * no I/O, starts no process, and opens no network connection.
 */
public final class Canary {
    private static volatile boolean fired;
    private static volatile String firedBy;

    private Canary() {
    }

    public static void fire(String by) {
        fired = true;
        firedBy = by;
    }

    public static boolean fired() {
        return fired;
    }

    public static String firedBy() {
        return firedBy;
    }
}
