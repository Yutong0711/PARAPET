package thirdparty.canary;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.Serializable;

/** Simulated third-party class whose readObject has a side effect (canary only). */
public class GadgetA implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String label;

    public GadgetA(String label) {
        this.label = label;
    }

    private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
        in.defaultReadObject();
        Canary.fire("GadgetA.readObject");
    }

    @Override
    public String toString() {
        return "GadgetA(" + label + ")";
    }
}
