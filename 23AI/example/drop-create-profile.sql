BEGIN
     DBMS_CLOUD_AI.DROP_PROFILE(profile_name => 'XPTO_AI');
END;


BEGIN
  DBMS_CLOUD_AI.CREATE_PROFILE(
    profile_name => 'XPTO_AI',
    attributes   => JSON_OBJECT(
      'provider'         VALUE 'oci',
      'credential_name'  VALUE 'XPTO_CRED',
      'model'            VALUE 'cohere.command-r-plus-08-2024',

      'object_list'      VALUE JSON_ARRAY(
        JSON_OBJECT('owner' VALUE 'XPTO_STORE', 'name' VALUE 'XPTO_CATEGORIAS'),
        JSON_OBJECT('owner' VALUE 'XPTO_STORE', 'name' VALUE 'XPTO_PRODUTOS'),
        JSON_OBJECT('owner' VALUE 'XPTO_STORE', 'name' VALUE 'XPTO_CLIENTES'),
        JSON_OBJECT('owner' VALUE 'XPTO_STORE', 'name' VALUE 'XPTO_VENDAS')
      ),

      'annotations'      VALUE TRUE
    )
  );
END;
