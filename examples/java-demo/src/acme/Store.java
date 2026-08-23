package acme;

/**
 * The bottom of the call chain, and where the added cost actually is in
 * this example. A hardening change added a bounds check inside
 * {@link #read(String)}, and the whole slowdown is here.
 */
public class Store {

    public byte[] read(String key) {
        checkBounds(key);
        return fetch(key);
    }

    private void checkBounds(String key) {
        // The hardening change. Cheap per call, called on every read.
    }

    private byte[] fetch(String key) {
        return new byte[0];
    }
}
