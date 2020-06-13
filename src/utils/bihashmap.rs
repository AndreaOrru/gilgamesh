/// Create a **BiHashMap** from a list of key-value pairs.
#[macro_export]
macro_rules! bihashmap {
    (@single $($x:tt)*) => (());
    (@count $($rest:expr),*) => (<[()]>::len(&[$(bihashmap!(@single $rest)),*]));

    ($($key:expr => $value:expr,)+) => { bihashmap!($($key => $value),+) };
    ($($key:expr => $value:expr),*) => {
        {
            let _cap = bihashmap!(@count $($key),*);
            let mut _map = ::bimap::BiHashMap::with_capacity(_cap);
            $(
                let _ = _map.insert($key, $value);
            )*
            _map
        }
    };
}
