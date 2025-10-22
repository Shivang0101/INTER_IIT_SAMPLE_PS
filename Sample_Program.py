import pathway as pw

def main():
    # 1. Create a static table directly from a Python list of lists.
    data = [
        [5, 10],
        [15, 20]
    ]
    
    # ✅ FIXED: Use table_from_rows instead of from_lists
    input_table = pw.debug.table_from_rows(
        schema=pw.schema_from_types(a=int, b=int),
        rows=[(row[0], row[1]) for row in data]
    )
    
    # 2. Transformation: Create a new column 'sum' by adding 'a' and 'b'.
    result_table = input_table.select(
        a=input_table.a,
        b=input_table.b,
        sum=input_table.a + input_table.b
    )
    
    # 3. Output: Print the resulting table to the console.
    pw.debug.compute_and_print(result_table)

if __name__ == "__main__":
    main()



#Output
"""
docker run -it --rm --name my-pathway-app my-pathway-app             
/usr/local/lib/python3.11/site-packages/fs/__init__.py:4: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  __import__("pkg_resources").declare_namespace(__name__)  # type: ignore
[2025-10-22T11:48:51]:INFO:Preparing Pathway computation
[2025-10-22T11:48:51]:INFO:subscribe-0: Done writing 2 entries, closing data sink. Current batch writes took: 0 ms. All writes so far took: 0 ms.
            | a  | b  | sum
^X1MXHYY... | 5  | 10 | 15
^YYY4HAB... | 15 | 20 | 35
"""