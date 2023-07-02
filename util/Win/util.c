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
		if(a[ai] != b[bi]){
			if(a[ai] >= '0' && a[ai] <= '9' && b[bi] >= '0' && b[bi] <= '9'){
				aval = bval = 0;
				while(a[ai] >= '0' && a[ai] <= '9' && ai < al){
					aval = (10*aval) + (a[ai] - '0');
					++ai;
				}
				while(b[bi] >= '0' && b[bi] <= '9' && bi < bl){
					bval = (10*bval) + (b[bi] - '0');
					++bi;
				}
				if(aval != bval){
					return aval > bval ? 1 : -1;
				}
				continue;
			}
			return a[ai] > b[bi] ? 1 : -1;
		}
		++ai;
		++bi;
	}
	return al > bl ? 1 : -1;
}