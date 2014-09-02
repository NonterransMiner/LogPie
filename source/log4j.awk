# This will make the pcregrep's output into a Python list object's readable form.

function take_msg (log_point) {
    return gensub(/\\((.+)\\);/, "\\\\1", "", log_point);
}

BEGIN { 
        FS=":";
        printf "[";
      }
      
      {   
          printf "{\"file\":\"%s\",\"lineno\":%d,\"source\":'''%s'''},\n",
                 $1, $2, take_msg($3)
      }
      
END   { printf "]" }
