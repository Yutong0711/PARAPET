package acme;

/** A cache in front of the store. Cheap on a hit, expensive on a miss. */
public class Cache {

    private Store store;

    public byte[] get(String key) {
        byte[] hit = lookup(key);
        if (hit != null) {
            return hit;
        }
        return store.read(key);
    }

    private byte[] lookup(String key) {
        return null;
    }
}
