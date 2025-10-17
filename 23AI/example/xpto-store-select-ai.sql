## showsql, runsql, narrate, explainsql, chat, feedback ##

SELECT DBMS_CLOUD_AI.GENERATE(
  action       => 'runsql',
  prompt       => 'top 3 produtos por receita em 2024',
  profile_name => 'XPTO_AI'
) AS result
FROM dual;

## ou ##

EXEC DBMS_CLOUD_AI.SET_PROFILE('XPTO_AI');
SELECT AI RUNSQL 'quais produtos foram adquiridos pelo cliente Carlos Souza, e em quais meses e quantidades?';
