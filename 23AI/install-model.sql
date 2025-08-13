DECLARE 
    ONNX_MOD_FILE VARCHAR2(100) := 'all_MiniLM_L12_v2.onnx';
    MODNAME VARCHAR2(500);
    LOCATION_URI VARCHAR2(300) := 'https://path/to/the/folder/where/the/model/file/is/available/';

BEGIN
    DBMS_OUTPUT.PUT_LINE('ONNX model file name in Object Storage is: '||ONNX_MOD_FILE); 

    -- Define o nome do modelo com base no nome do arquivo
    SELECT UPPER(REGEXP_SUBSTR(ONNX_MOD_FILE, '[^.]+')) INTO MODNAME FROM dual;
    DBMS_OUTPUT.PUT_LINE('Model will be loaded and saved with name: '||MODNAME);

    -- Drop do modelo anterior, se existir
    BEGIN DBMS_DATA_MINING.DROP_MODEL(model_name => MODNAME);
    EXCEPTION WHEN OTHERS THEN NULL; END;

    -- Download do modelo do Object Storage para o banco
    DBMS_CLOUD.GET_OBJECT(                            
        credential_name => NULL,
        directory_name => 'DATA_PUMP_DIR',
        object_uri => LOCATION_URI || ONNX_MOD_FILE);

    -- Registro do modelo no banco
    DBMS_VECTOR.LOAD_ONNX_MODEL(
        directory => 'DATA_PUMP_DIR',
        file_name => ONNX_MOD_FILE,
        model_name => MODNAME);

    DBMS_OUTPUT.PUT_LINE('New model successfully loaded with name: '||MODNAME);
END;
