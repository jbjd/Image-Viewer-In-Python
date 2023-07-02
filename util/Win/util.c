// gcc util.c -c
// gcc -shared -o util.dll util.o
#include <wchar.h>

int myCmpW(const wchar_t* a, const wchar_t* b){
	if(!a){
		if(!b){
			return 0;
		}
		return -1;
	}
	if(!b){ 
		return 1;
	}
	unsigned long long al = wcslen(a), bl = wcslen(b), ai = 0, bi = 0, aval, bval;

	while(ai < al && bi < bl){
		if(iswdigit(a[ai]) && iswdigit(b[bi])){
			aval = bval = 0;
			while(iswdigit(a[ai]) && ai < al){
				aval = (10*aval) + (a[ai] - L'0');
				++ai;
			}
			while(iswdigit(b[bi]) && bi < bl){
				bval = (10*bval) + (b[bi] - L'0');
				++bi;
			}
			if(aval != bval){
				return aval > bval ? 1 : -1;
			}
			continue;
		}
		if(a[ai] != b[bi]){
			return a[ai] > b[bi] ? 1 : -1;
		}
		++ai;
		++bi;
	}
	return al > bl ? 1 : -1;
}