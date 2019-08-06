from DownloadStation import MyDownloadStation as DD

__dsms = {'host':'192.168.1.1',
          'port':'5001',
          'https': True ,
          'username':'your username',
          'password':'your password'}
fn = u"E:\\MyCoding\\D_Check\\HQ.torrent"
with DD() as a :
    a.CONNECT(dsm = __dsms)
    b = a.AddTask(file = fn)
del a
print ('Download HQ.torrent OK? ',b)
