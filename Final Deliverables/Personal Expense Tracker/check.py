import ibm_db
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=fbd88901-ebdb-4a4f-a32e-9822b9fb237b.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32731;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=dxy32089;PWD=75PDKFFPQjkfYtNz",'','')

stmt = ibm_db.exec_immediate(conn, "Select * from records where email = '1912019@nec.edu.in';")
result = ibm_db.fetch_assoc(stmt)
records = []
cnt = 1
while result!=False:
#     record.append([result["AMOUNT"],result["EMAIL"],result["TYPE"]])
    records.append([cnt,result["EMAIL"],result["AMOUNT"],result["TO_ACC"],result["TYPE"],result["CATEGORY"]])
    result = ibm_db.fetch_assoc(stmt)
    cnt+=1

for x in records:
    print(x[0])