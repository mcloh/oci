This README outlines the steps to load the HuggingFace sentence-transformers model 'all-MiniLM-L12-v2' into an Oracle Database 23ai on-premises or Oracle Database cloud instance. This model is augmented to include pre- and post-processing steps for producing embeddings using the in-database ONNX Runtime engine.

Instructions for loading the augmented all-MiniLM-L12-v2 model into Oracle Database:

1. Unzip the file

$ unzip all-MiniLM-L12-v2_augmented.zip
Archive:  all-MiniLM-L12-v2_augmented.zip
  inflating: all_MiniLM_L12_v2.onnx
  inflating: README-ALL_MINILM_L12_V2-augmented.txt

2. Log into your database instance as sysdba. In this example, we are logging into a pluggable database named ORCLPDB.

$ sqlplus / as sysdba;

SQL> alter session set container=ORCLPDB;

3. Apply grants and define the data dump directory as the path where the ONNX model was unzipped. 

Note, in this example, we are using the OMLUSER schema. Replace OMLUSER with your schema name.

SQL> GRANT DB_DEVELOPER_ROLE, CREATE MINING MODEL TO OMLUSER;
SQL> CREATE OR REPLACE DIRECTORY DM_DUMP AS '<path to ONNX model>';
SQL> GRANT READ ON DIRECTORY DM_DUMP TO OMLUSER;
SQL> GRANT WRITE ON DIRECTORY DM_DUMP TO OMLUSER;
SQL> exit

4. Log into your schema.

$ sqlplus omluser/omluser@ORCLPDB;

Load the ONNX model. Optionally drop the model first if a model with the same name already exists in the database.

SQL> exec DBMS_VECTOR.DROP_ONNX_MODEL(model_name => 'ALL_MINILM_L12_V2', force => true);

BEGIN
   DBMS_VECTOR.LOAD_ONNX_MODEL(
        directory => 'DM_DUMP',
		file_name => 'all_MiniLM_L12_v2.onnx',
        model_name => 'ALL_MINILM_L12_V2',
        metadata => JSON('{"function" : "embedding", "embeddingOutput" : "embedding", "input": {"input": ["DATA"]}}'));
END;
/

5. Validate that the model was imported to the database.

SQL> select model_name, algorithm, mining_function from user_mining_models where  model_name='ALL_MINILM_L12_V2';

MODEL_NAME         ALGORITHM     MINING_FUNCTION
----------         ---------     ---------------
ALL_MINILM_L12_V2  ONNX          EMBEDDING

6. Generate embedding vectors using the VECTOR_EMBEDDING SQL scoring function. Partial output is shown below.

SQL> SELECT VECTOR_EMBEDDING(ALL_MINILM_L12_V2 USING 'The quick brown fox jumped' as DATA) AS embedding;

EMBEDDING
--------------------------------------------------------------------------------
[1.40532674E-002,-4.24734354E-002,-1.42729701E-002,3.90004814E-002,3.84781733E-0
02,-7.44695729E-003,-1.20800901E-002,2.60837115E-002,-3.97795811E-002,3.85206044
E-002,-8.92989617E-003,-5.55456802E-002,5.72643466E-002,3.43147628E-002,-3.51916
...
...
...


7. An Alternate method to import ONNX Models is to use the DBMS_DATA_MINING.IMPORT_ONNX_MODEL procedure. 

This example sets up a BLOB object and a BFILE locator, creates a temporary BLOB for storing the ONNX file from the DM_DUMP directory, and reads its contents into the BLOB. It then closes the file and uses the content to import an ONNX model into the database with specified metadata, before releasing the temporary BLOB resources.

SQL> exec DBMS_VECTOR.DROP_ONNX_MODEL(model_name => 'ALL_MINILM_L12_V2', force => true);

DECLARE
    m_blob BLOB default empty_blob();
    m_src_loc BFILE ;
    BEGIN
    DBMS_LOB.createtemporary (m_blob, FALSE);
    m_src_loc := BFILENAME('DM_DUMP', 'all_MiniLM_L12_v2.onnx');
    DBMS_LOB.fileopen (m_src_loc, DBMS_LOB.file_readonly);
    DBMS_LOB.loadfromfile (m_blob, m_src_loc, DBMS_LOB.getlength (m_src_loc));
    DBMS_LOB.CLOSE(m_src_loc);
    DBMS_DATA_MINING.import_onnx_model ('ALL_MINILM_L12_V2', 
                                        m_blob, 
                                        JSON('{"function":"embedding", "embeddingOutput":"embedding", "input":{"input": ["DATA"]}}'));
    DBMS_LOB.freetemporary (m_blob);
    END;
    /


Follow steps 5 and 6 above to validate the model was imported to the database and to generate embedding vectors.

For more information, refer to the Oracle AI Vector Search User's Guide
https://docs.oracle.com/en/database/oracle/oracle-database/23/vecse/import-onnx-models-oracle-database-end-end-example.html
