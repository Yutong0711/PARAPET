package acme;

/**
 * Loads records by name. The cost of a load is almost entirely the cost of
 * what it calls, which is what makes it the Expensive Callee in this
 * example.
 */
public class Loader {

    private Cache cache;
    private Decoder decoder;

    public byte[] load(String name) {
        byte[] raw = cache.get(name);
        return decoder.decode(raw);
    }

    public byte[] loadAll(String prefix) {
        return load(prefix);
    }
}
