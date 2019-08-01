# coding: utf-8

import requests
class DownloadStation :
    def __init__(self,host = '',port = '',https = False, username = '' ,password = '') :
        self.DSconnection = requests.session()
        self.dsm = {'host'    : host ,
                    'port'    :port,
                    'https'   :https ,
                    'username':username,
                    'password':password
                   }
        if host != '' :
            self.CONNECT (self.dsm)
    def CONNECT (self,dsm = {}):
        self.dsm.update(dsm)
        host    = self.dsm['host']
        port    = self.dsm['port']
        https   = self.dsm['https']
        username= self.dsm['username']
        password= self.dsm['password']
        self.url= 'http{}://{}:{}/webapi'.format('s' if https else '', host,port)
        Query_PL= {'api' : 'SYNO.API.Info',
                   'version' : '1',
                   'method' : 'query' , 
                   'query' : 'ALL'
                  }
        try :
            q = self.DSconnection.get('{}/{}'.format (self.url,'/query.cgi'),params = Query_PL ,verify = False, timeout = 7).json()
            #查詢 Auth API版本
            Auth_version = q['data']['SYNO.API.Auth']['maxVersion']
            Auth_path = q['data']['SYNO.API.Auth']['path']
            #查詢 Task API版本            
            Task_version = q['data']['SYNO.DownloadStation.Task']['maxVersion']
            Task_Path = q['data']['SYNO.DownloadStation.Task']['path']
        except Exception as e:
            print (e)
            self.SID    = ''
            Task_Path   = 'DownloadStation/task.cgi'
            Task_version= '1'
            Auth_path   = 'auth.cgi'
            Auth_version= '1'
        finally :
            self.Task_url= '{}/{}'.format(self.url,Task_Path)
            self.Task_PL = {'api' : 'SYNO.DownloadStation.Task' ,
                            'version' : Task_version
                           }
            self.Auth_url= '{}/{}'.format(self.url , Auth_path)
            self.Auth_PL = {'api' : 'SYNO.API.Auth' ,
                            'version' : Auth_version ,
                            'method' : 'login',
                            'account' : '' ,
                            'passwd' : '' ,
                            'session' : 'DownloadStation' ,
                            'format' : 'cookie' #用 'sid' 會失敗
                           }
            self.SID = self.AUTH(username = username , password = password)
    def AUTH (self ,username = '' , password = '') :
        '''身份驗證
        成功 : return sid
        失敗 : return ''
        '''
        if (username == '') or (password == '' ):
            return ''
        else :
            Auth_PL =  self.Auth_PL.copy()
            Auth_PL.update({'account' : username ,
                            'passwd'  : password  })
            try :
                A = self.DSconnection.get (self.Auth_url,params = Auth_PL ,verify = False,timeout = 7)
                return A.json()['data']['sid']
            except :
                return ''
    def AddTask (self,uri = None, file = None, des = '') :
    '''
    uri     : 指定的檔案連結 http: , ftp: ,magnet:....
    file    : 指定的torrent檔案(包括路徑)
    des     : 檔案下載目的資料夾
    '''
        TP = self.Task_PL.copy()
        #設定方法為 create
        TP.update({'method' : 'create'})
        if self.SID != '' :
            #新增 Task
            #製作 mutipart 之特製格式 
            #       { <name> : (filename, data [, content_type[, headers]])}
            TF = { 'api'       :(None , TP['api'])
                  ,'version'   :(None , str(TP['version']))
                  ,'method'    :(None , TP['method'])
                  #必須指定sid ,否則會出現error : code : 105
                  ,'_sid'      :(None , self.SID)
                  }
            if des != '' :
                TP.update({'destination' : des} )
                TF.update({'destination' :(None,des)})
            if  uri != None :
                try :
                    TP.update( {'uri' : uri} )
                    CP = self.DSconnection.get (self.Task_url,params = TP ,verify = False, timeout = 7)
                except :
                    return False
                return CP.json()['success']
            elif file != None :
                try :
                    with open (file,'rb') as f:
                        #取得檔案名稱
                        if '\\' in file :
                            fn = file.split('\\')[-1]
                        elif '/' in file :
                            fn = file.split('/')[-1]
                        else :
                            fn = file
                        #檔案參數必須是最後一個
                        TF.update({'file':(fn,f,'application/octet-stream')})
                        #準備發送本體，headers 由prepare自動產生，勿自行添加
                        pp = requests.Request('POST',self.Task_url)
                        pp.files = TF
                        ppd = pp.prepare()
                        #本體可查見 ppd.body
                        #發送本體
                        CP = self.DSconnection.send (ppd , verify = False , timeout = 20) 
                except :
                    return False
                return CP.json()['success']
            else :
                return False
        else :
            return False
    def List (self,offset = 0):
        '''
        offset : 取回第 (offset + 1) 筆(含)之後資料
        return 字典
                {'success' : True / False ,
                 'data' : { 'total' : 回傳總數 ,
                            'offset': 偏移值 ,
                            'tasks': [{    'id': 工作ID, 
                                           'type':下載形式, 
                                           'username':工作建立者, 
                                           'title':工作名稱, 
                                           'size':所需傳輸總數, 
                                           'status':下載狀態, 
                                           'status_extra':其他狀態, 
                                           'additional': { "file": [ {   "filename":檔案名稱, 
                                                                         "priority":優先順序, 
                                                                         "size":檔案大小, 
                                                                         "size_downloaded":已下載大小
                                                                     }
                                                            "detail":{   "uri":下載連結
                                                                        }
                                                                   ]
                                                        }
                                      }
                                     ]
                          }
                }
        '''
        TP = self.Task_PL.copy()
        TP.update({'method': 'list' ,
                   'offset': offset ,
                   'additional' : 'file,detail'
                  })
        try :
            CP = self.DSconnection.get (self.Task_url , params = TP ,verify = False, timeout = 7)
            return CP.json()
        except :
            return {'success' : False }
    def GetInfo (self, task_id):
        '''
        return 字典
                {'success' : True / False ,
                 'data' : { 'tasks': [{    'id': 工作ID, 
                                           'type':下載形式, 
                                           'username':工作建立者, 
                                           'title':工作名稱, 
                                           'size':所需傳輸總數, 
                                           'status':下載狀態  }
                                   ]
                          }
                }
        '''
        TP = self.Task_PL.copy()
        TP.update({'method': 'getinfo' ,
                   'id': task_id,
                   'additional' : 'detail'
                  })
        try :
            CP = self.DSconnection.get (self.Task_url , params = TP ,verify = False, timeout = 7)
            return CP.json()
        except :
            return {'success' : False }
    def Delete (self,task_id) :
    #本段程式尚未測試
        TP = self.Task_PL.copy()
        TP.update({'method': 'delete' ,
                   'id': task_id ,
                   'force_complete' : False
                  })
        try :
            CP = self.DSconnection.get (self.Task_url , params = TP ,verify = False, timeout = 7)
            '''
            {
                'success' : True / False
                'data': [
                            {
                                'error' : 0 表示成功
                                'id' : 被刪除的 ID
                            }
                        ]
            }
            '''
            return CP.json()['success']
        except :
            return False
    def close (self):
        pass
    def __enter__ (self) :
        return self
    def __exit__(self, exc_ty, exc_val, tb) :
        try :
            self.DSconnection.close()
        except :
            pass
    def __del__ (self) :
        try :
            self.DSconnection.close()
        except :
            pass
