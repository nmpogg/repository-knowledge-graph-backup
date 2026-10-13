package com.example.rkgfixture.orders.analysiscases.negative;

import java.util.*;

// Expected: resolve only language-valid wildcard imports; never guess an ambiguous simple name.
public final class WildcardImportCase {
    public List<String> copy(Collection<String> values) {
        return new ArrayList<>(values);
    }
}
