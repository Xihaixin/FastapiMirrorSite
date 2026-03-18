function $$_nodclk(g, cid) {
       if ($$_cnode) {
           $$_bgc($$_cnode.id + '_t', 'transparent');
       }
       var d = $$(g);
       $$_cnode = d;
       $$_bgc(d.id + '_t', '#BBDDFF');
       if (d.style.display == 'block') {
           $$_bgi(d.id + '_b', "url('/site/pub/img/1966.gif')");
           d.style.display = 'none';
       } else {
           if (!d.D) {
               var x = $$req();
               if (x) {
                   try {
                       var url = '/auto/db/jsearch.aspx?db=' + $$_cdb + '&agfi=' + $$_cagfi + '&agname=' + $$_cagname + $$_mstsetting + '&cls=' + $$_clas + '&cid=' + cid + '&wrd=' + $$_cwrd + '&count=' + $$_count + '&d=' + $$date();
                       x.open('get', url, false);
                       x.onreadystatechange = function() {
                           if (x.readyState == 4 && x.status == 200) {
                               if (x.responseText != '') {
                                   d.D = x.responseText.split('\r');
                                   if (d.D && d.D[0] && d.D[0] == '1' && d.D[7]) {
                                       d.innerHTML = d.D[7];
                                   }
                               }
                           }
                       }
                       ;
                       x.send('');
                   } catch (ex) {
                       alert(ex);
                       return;
                   }
               }
           }
           $$_bgi(d.id + '_b', "url('/site/pub/img/1976.gif')");
           if (d.innerHTML != '') {
               d.style.display = 'block';
           }
       }
       if (d.D && d.D[0] && d.D[0] == '1') {
           $$_subkey = '';
           $$_lmttype = '0';
           $$_fidnode = null;
           $$_ft0node = null;
           $$_ft1node = null;
           $$_ft2node = null;
           if (d.D[1]) {
               $$_crkey = d.D[1];
           }
           if (d.D[2]) {
               $$('mp_cn_rdhit').innerHTML = d.D[2];
           }
           if (d.D[3]) {
               $$('mp_cn_rddiv').innerHTML = d.D[3];
           }
           if (d.D[4]) {
               $$('mp_cn_nextpage').innerHTML = d.D[4];
           }
           if (d.D[5]) {
               $$('mp_cn_searchpoint').innerHTML = d.D[5];
           }
           if (d.D[6]) {
               $$('mp_cn_feature').innerHTML = d.D[6];
           } else {
               $$('mp_cn_feature').innerHTML = '';
           }
           if (d.D[8]) {
               $$_aggid = d.D[8];
           }
       }
   }